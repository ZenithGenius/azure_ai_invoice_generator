"""
Invoice Queue System - Background Processing Module
=================================================

Handles background invoice generation with Redis queue and worker pool.
Provides real-time status updates and job tracking.
"""

import json
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis
except ImportError:
    redis = None
    print("⚠️ Redis not available - queue functionality will be limited")


class JobStatus(Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InvoiceJob:
    """Invoice generation job data structure."""
    job_id: str
    order_details: Dict
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InvoiceJob':
        """Create job from dictionary."""
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        data['status'] = JobStatus(data['status'])
        return cls(**data)


class InvoiceQueue:
    """Redis-based invoice generation queue with worker pool."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", max_workers: int = 3):
        """Initialize the invoice queue."""
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.worker_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.status_callbacks: List[Callable] = []
        self.is_running = False
        self.worker_thread = None
        
        # Initialize memory fallback first
        self._memory_queue = []
        self._memory_jobs = {}
        
        # Initialize Redis client
        if redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                print(f"✅ Connected to Redis at {redis_url}")
            except Exception as e:
                print(f"❌ Failed to connect to Redis: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
            print("⚠️ Redis not available - using in-memory fallback")
    
    def add_status_callback(self, callback: Callable[[InvoiceJob], None]):
        """Add callback for job status updates."""
        self.status_callbacks.append(callback)
    
    def _notify_status_change(self, job: InvoiceJob):
        """Notify all callbacks of job status change."""
        for callback in self.status_callbacks:
            try:
                callback(job)
            except Exception as e:
                print(f"Error in status callback: {e}")
    
    def enqueue_invoice(self, order_details: Dict, priority: int = 0) -> str:
        """Add invoice generation job to queue."""
        job_id = str(uuid.uuid4())
        
        job = InvoiceJob(
            job_id=job_id,
            order_details=order_details,
            status=JobStatus.QUEUED,
            created_at=datetime.now()
        )
        
        if self.redis_client:
            # Add to Redis queue with priority
            queue_item = {
                "job_id": job_id,
                "priority": priority,
                "created_at": job.created_at.isoformat()
            }
            
            # Store job details - convert to JSON string
            job_data = job.to_dict()
            for key, value in job_data.items():
                if isinstance(value, (dict, list)):
                    job_data[key] = json.dumps(value)
                elif value is None:
                    job_data[key] = ""
                else:
                    job_data[key] = str(value)
            
            self.redis_client.hset(f"job:{job_id}", mapping=job_data)
            
            # Add to priority queue
            self.redis_client.zadd("invoice_queue", {json.dumps(queue_item): priority})
            
            print(f"📝 Enqueued invoice job {job_id} with priority {priority}")
        else:
            # Fallback to memory
            self._memory_jobs[job_id] = job
            self._memory_queue.append((priority, job_id))
            self._memory_queue.sort(reverse=True)  # Higher priority first
        
        self._notify_status_change(job)
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[InvoiceJob]:
        """Get current job status."""
        if self.redis_client:
            job_data = self.redis_client.hgetall(f"job:{job_id}")
            if job_data:
                # Convert back from Redis format
                processed_data = {}
                for key, value in job_data.items():
                    if key in ['order_details', 'result'] and value:
                        try:
                            processed_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            processed_data[key] = value
                    elif key in ['created_at', 'started_at', 'completed_at'] and value:
                        try:
                            processed_data[key] = datetime.fromisoformat(value)
                        except ValueError:
                            processed_data[key] = None
                    elif key == 'status':
                        try:
                            processed_data[key] = JobStatus(value)
                        except ValueError:
                            processed_data[key] = JobStatus.QUEUED
                    elif key in ['progress', 'retry_count', 'max_retries']:
                        try:
                            processed_data[key] = float(value) if key == 'progress' else int(value)
                        except ValueError:
                            processed_data[key] = 0.0 if key == 'progress' else 0
                    else:
                        processed_data[key] = value
                
                return InvoiceJob(**processed_data)
        else:
            return self._memory_jobs.get(job_id)
        
        return None
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         progress: float = None, result: Dict = None, error: str = None):
        """Update job status and notify callbacks."""
        job = self.get_job_status(job_id)
        if not job:
            return
        
        job.status = status
        if progress is not None:
            job.progress = progress
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        
        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now()
        
        # Save updated job
        if self.redis_client:
            # Convert to Redis format
            job_data = job.to_dict()
            for key, value in job_data.items():
                if isinstance(value, (dict, list)):
                    job_data[key] = json.dumps(value)
                elif value is None:
                    job_data[key] = ""
                else:
                    job_data[key] = str(value)
            
            self.redis_client.hset(f"job:{job_id}", mapping=job_data)
        else:
            self._memory_jobs[job_id] = job
        
        self._notify_status_change(job)
    
    def start_workers(self):
        """Start background worker thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print(f"🚀 Started {self.max_workers} invoice generation workers")
    
    def stop_workers(self):
        """Stop background workers."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
        self.worker_pool.shutdown(wait=True)
        print("🛑 Stopped invoice generation workers")
    
    def _worker_loop(self):
        """Main worker loop to process jobs."""
        while self.is_running:
            try:
                job_id = self._get_next_job()
                if job_id:
                    # Submit job to thread pool
                    future = self.worker_pool.submit(self._process_job, job_id)
                    if future:
                        print(f"🔄 Submitted job {job_id} to worker pool")
                    else:
                        print(f"❌ Failed to submit job {job_id} to worker pool")
                    # Don't wait for completion - let it run in background
                else:
                    # No jobs available, wait a bit
                    time.sleep(1)
            except Exception as e:
                print(f"Error in worker loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _get_next_job(self) -> Optional[str]:
        """Get next job from queue."""
        if self.redis_client:
            # Get highest priority job
            items = self.redis_client.zrevrange("invoice_queue", 0, 0, withscores=True)
            if items:
                queue_item_str, priority = items[0]
                queue_item = json.loads(queue_item_str)
                job_id = queue_item["job_id"]
                
                # Remove from queue
                self.redis_client.zrem("invoice_queue", queue_item_str)
                return job_id
        else:
            # Memory fallback
            if self._memory_queue:
                priority, job_id = self._memory_queue.pop(0)
                return job_id
        
        return None
    
    def _process_job(self, job_id: str):
        """Process a single invoice generation job."""
        try:
            job = self.get_job_status(job_id)
            if not job:
                print(f"❌ Job {job_id} not found")
                return
            
            print(f"🔄 Processing invoice job {job_id}")
            self.update_job_status(job_id, JobStatus.PROCESSING, progress=0.0)
            
            # Import here to avoid circular imports
            from service_manager import get_service_manager
            
            service_manager = get_service_manager()
            
            # Update progress
            self.update_job_status(job_id, JobStatus.PROCESSING, progress=0.2)
            
            # Generate invoice using enhanced AI system
            result = service_manager.enhanced_ai_generate(
                self._create_invoice_prompt(job.order_details),
                context=job.order_details
            )
            
            self.update_job_status(job_id, JobStatus.PROCESSING, progress=0.6)
            
            if result.get("success"):
                # Process successful result
                invoice_data = self._extract_invoice_data(result["response"])
                
                # Save invoice
                storage_result = service_manager.save_invoice(invoice_data)
                
                self.update_job_status(job_id, JobStatus.PROCESSING, progress=0.9)
                
                final_result = {
                    "success": True,
                    "invoice_data": invoice_data,
                    "storage_result": storage_result,
                    "method": "queue_processed"
                }
                
                self.update_job_status(
                    job_id, 
                    JobStatus.COMPLETED, 
                    progress=1.0, 
                    result=final_result
                )
                
                print(f"✅ Successfully processed invoice job {job_id}")
            else:
                raise Exception(f"AI generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to process job {job_id}: {error_msg}")
            
            job = self.get_job_status(job_id)
            if job and job.retry_count < job.max_retries:
                # Retry the job
                job.retry_count += 1
                self.update_job_status(job_id, JobStatus.QUEUED)
                
                # Re-enqueue with lower priority
                if self.redis_client:
                    queue_item = {
                        "job_id": job_id,
                        "priority": -job.retry_count,  # Lower priority for retries
                        "created_at": job.created_at.isoformat()
                    }
                    self.redis_client.zadd("invoice_queue", {json.dumps(queue_item): -job.retry_count})
                else:
                    self._memory_queue.append((-job.retry_count, job_id))
                    self._memory_queue.sort(reverse=True)
                
                print(f"🔄 Retrying job {job_id} (attempt {job.retry_count + 1}/{job.max_retries + 1})")
            else:
                # Max retries reached
                self.update_job_status(
                    job_id, 
                    JobStatus.FAILED, 
                    error=error_msg
                )
    
    def _create_invoice_prompt(self, order_details: Dict) -> str:
        """Create AI prompt for invoice generation."""
        return f"""
Generate a professional invoice with the following details:

Client: {order_details.get('client_name', 'N/A')}
Email: {order_details.get('client_email', 'N/A')}
Address: {order_details.get('client_address', 'N/A')}

Items: {json.dumps(order_details.get('items', []), indent=2)}

Currency: {order_details.get('currency', 'USD')}
Tax Rate: {order_details.get('tax_rate', 0.0) * 100}%
Payment Terms: {order_details.get('payment_terms', 'Net 30')}

Please generate a complete invoice with proper formatting and calculations.
"""
    
    def _extract_invoice_data(self, ai_response: str) -> Dict:
        """Extract structured invoice data from AI response."""
        # This is a simplified extraction - in practice, you'd use more sophisticated parsing
        from generate_invoices import InvoiceGenerationSystem
        
        generator = InvoiceGenerationSystem()
        # Use the existing extraction logic
        return generator._extract_invoice_data_from_response(ai_response)
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        stats = {
            "queue_length": 0,
            "processing_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_jobs": 0
        }
        
        if self.redis_client:
            stats["queue_length"] = self.redis_client.zcard("invoice_queue")
            
            # Count jobs by status
            for status in JobStatus:
                pattern = f"job:*"
                jobs = self.redis_client.scan_iter(match=pattern)
                for job_key in jobs:
                    job_data = self.redis_client.hgetall(job_key)
                    if job_data.get("status") == status.value:
                        if status == JobStatus.PROCESSING:
                            stats["processing_jobs"] += 1
                        elif status == JobStatus.COMPLETED:
                            stats["completed_jobs"] += 1
                        elif status == JobStatus.FAILED:
                            stats["failed_jobs"] += 1
                        stats["total_jobs"] += 1
        else:
            stats["queue_length"] = len(self._memory_queue)
            stats["total_jobs"] = len(self._memory_jobs)
            
            for job in self._memory_jobs.values():
                if job.status == JobStatus.PROCESSING:
                    stats["processing_jobs"] += 1
                elif job.status == JobStatus.COMPLETED:
                    stats["completed_jobs"] += 1
                elif job.status == JobStatus.FAILED:
                    stats["failed_jobs"] += 1
        
        return stats
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        job = self.get_job_status(job_id)
        if not job:
            return False
        
        if job.status == JobStatus.QUEUED:
            self.update_job_status(job_id, JobStatus.CANCELLED)
            
            # Remove from queue if still there
            if self.redis_client:
                # Find and remove from queue
                items = self.redis_client.zrange("invoice_queue", 0, -1)
                for item_str in items:
                    item = json.loads(item_str)
                    if item["job_id"] == job_id:
                        self.redis_client.zrem("invoice_queue", item_str)
                        break
            else:
                self._memory_queue = [(p, jid) for p, jid in self._memory_queue if jid != job_id]
            
            return True
        
        return False  # Can't cancel jobs that are already processing


# Global queue instance
_invoice_queue = None


def get_invoice_queue() -> InvoiceQueue:
    """Get global invoice queue instance."""
    global _invoice_queue
    if _invoice_queue is None:
        _invoice_queue = InvoiceQueue()
        _invoice_queue.start_workers()
    return _invoice_queue


def cleanup_invoice_queue():
    """Cleanup global queue instance."""
    global _invoice_queue
    if _invoice_queue:
        _invoice_queue.stop_workers()
        _invoice_queue = None 