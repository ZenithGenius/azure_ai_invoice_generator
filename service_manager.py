"""
Centralized Service Manager
==========================

This module provides a centralized service manager that implements singleton pattern
for all Azure services, eliminating redundant initializations and API calls.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import random
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import (
    ServiceRequestError,
    HttpResponseError,
    ResourceNotFoundError,
    ClientAuthenticationError,
)

import config
from cosmos_service import CosmosDBService
from azure_search_service import AzureSearchService


class RateLimitHandler:
    """Advanced rate limit and retry handler for AI services."""

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = AdaptiveRateLimiter()

    def with_retry(self, max_retries=5, base_delay=1.0, max_delay=60.0):
        """Decorator for intelligent retry with exponential backoff."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(max_retries):
                    try:
                        # Check circuit breaker
                        if not self.circuit_breaker.can_execute():
                            raise Exception(
                                "Circuit breaker is open - service temporarily unavailable"
                            )

                        # Check rate limits
                        if not self.rate_limiter.can_proceed():
                            delay = self.rate_limiter.get_delay()
                            print(f"⏳ Rate limit reached, waiting {delay:.1f}s...")
                            time.sleep(delay)

                        # Execute function
                        result = func(*args, **kwargs)

                        # Success - reset circuit breaker
                        self.circuit_breaker.record_success()
                        self.rate_limiter.record_success()

                        return result

                    except Exception as e:
                        last_exception = e
                        error_type = self._classify_error(e)

                        # Record failure
                        self.circuit_breaker.record_failure()

                        if error_type == "rate_limit":
                            # Exponential backoff for rate limits
                            delay = min(
                                base_delay * (2**attempt) + random.uniform(0, 1),
                                max_delay,
                            )
                            print(
                                f"🔄 Rate limit hit (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
                            )
                            time.sleep(delay)
                            self.rate_limiter.record_rate_limit()

                        elif error_type == "transient":
                            # Linear backoff for transient errors
                            delay = min(base_delay * (attempt + 1), max_delay)
                            print(
                                f"🔄 Transient error (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
                            )
                            time.sleep(delay)

                        elif error_type == "permanent":
                            # Don't retry permanent errors
                            print(f"❌ Permanent error detected: {str(e)}")
                            break

                        else:
                            # Default retry strategy
                            delay = min(base_delay * (1.5**attempt), max_delay)
                            print(
                                f"🔄 Error (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
                            )
                            time.sleep(delay)

                # All retries exhausted
                print(f"❌ All {max_retries} retry attempts failed")
                raise last_exception

            return wrapper

        return decorator

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate retry strategy."""
        error_str = str(error).lower()

        if any(
            keyword in error_str
            for keyword in [
                "rate limit",
                "too many requests",
                "quota exceeded",
                "throttled",
            ]
        ):
            return "rate_limit"
        elif any(
            keyword in error_str
            for keyword in [
                "timeout",
                "connection",
                "network",
                "temporary",
                "service unavailable",
            ]
        ):
            return "transient"
        elif any(
            keyword in error_str
            for keyword in [
                "authentication",
                "authorization",
                "forbidden",
                "not found",
                "invalid",
            ]
        ):
            return "permanent"
        else:
            return "unknown"


class CircuitBreaker:
    """Circuit breaker pattern for AI service protection."""

    def __init__(self, failure_threshold=5, recovery_timeout=60, half_open_max_calls=3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                return True
            return False
        elif self.state == "HALF_OPEN":
            return self.half_open_calls < self.half_open_max_calls

        return False

    def record_success(self):
        """Record successful execution."""
        if self.state == "HALF_OPEN":
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = "CLOSED"
                self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (
            datetime.now() - self.last_failure_time
        ).total_seconds() > self.recovery_timeout


class AdaptiveRateLimiter:
    """Adaptive rate limiter that learns from API responses."""

    def __init__(self):
        self.requests_per_minute = 60  # Start conservative
        self.last_request_time = None
        self.request_count = 0
        self.window_start = datetime.now()
        self.consecutive_successes = 0
        self.consecutive_rate_limits = 0

    def can_proceed(self) -> bool:
        """Check if request can proceed."""
        now = datetime.now()

        # Reset window if needed
        if (now - self.window_start).total_seconds() >= 60:
            self.request_count = 0
            self.window_start = now

        return self.request_count < self.requests_per_minute

    def record_success(self):
        """Record successful request."""
        self.request_count += 1
        self.last_request_time = datetime.now()
        self.consecutive_successes += 1
        self.consecutive_rate_limits = 0

        # Gradually increase rate limit if consistently successful
        if self.consecutive_successes >= 10:
            self.requests_per_minute = min(120, self.requests_per_minute + 5)
            self.consecutive_successes = 0

    def record_rate_limit(self):
        """Record rate limit hit."""
        self.consecutive_rate_limits += 1
        self.consecutive_successes = 0

        # Decrease rate limit more aggressively
        reduction = min(20, self.consecutive_rate_limits * 5)
        self.requests_per_minute = max(10, self.requests_per_minute - reduction)

    def get_delay(self) -> float:
        """Get delay before next request."""
        if self.last_request_time is None:
            return 0

        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        min_interval = 60.0 / self.requests_per_minute

        if time_since_last < min_interval:
            return min_interval - time_since_last
        return 0


class ServiceManager:
    """Centralized service manager with singleton pattern and caching."""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        """Implement singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service manager with enhanced error handling."""
        if ServiceManager._initialized:
            return

        print("🔄 Initializing Service Manager...")

        # Initialize rate limiting system
        self.rate_limit_handler = RateLimitHandler()

        # Initialize services
        self._initialize_services()
        self._initialize_cache()

        ServiceManager._initialized = True
        print("✅ Service Manager initialized successfully")

    def _initialize_services(self):
        """Initialize all services once."""
        print("🔄 Initializing centralized service manager...")

        # Initialize core services
        self.cosmos_service = None
        self.search_service = None
        self.ai_project_client = None
        self.blob_service = None
        self.agent = None

        # Service availability flags
        self.services_available = {
            "cosmos": False,
            "search": False,
            "ai_project": False,
            "blob_storage": False,
            "agent": False,
        }

        # Initialize services with error handling
        self._init_cosmos_service()
        self._init_search_service()
        self._init_ai_project_client()
        self._init_blob_service()
        self._init_agent()

        print("✅ Service manager initialized successfully")

    def _initialize_cache(self):
        """Initialize advanced caching system with LRU and statistics."""
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_access_count = {}
        self.cache_hit_count = {}
        self.cache_miss_count = {}

        # Enhanced TTL configuration with different cache types
        self.cache_ttl = {
            "statistics": 300,  # 5 minutes - frequently changing data
            "invoice_list": 180,  # 3 minutes - moderately changing data
            "search_results": 120,  # 2 minutes - search results can change
            "invoice_detail": 600,  # 10 minutes - individual invoices change less
            "client_data": 900,  # 15 minutes - client info is relatively stable
            "agent_config": 3600,  # 1 hour - agent configuration rarely changes
            "service_status": 60,  # 1 minute - service status can change quickly
        }

        # Cache size limits (LRU eviction)
        self.cache_max_size = {
            "statistics": 10,
            "invoice_list": 20,
            "search_results": 50,
            "invoice_detail": 100,
            "client_data": 200,
            "agent_config": 5,
            "service_status": 5,
        }

        # Cache performance tracking
        self.cache_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "cleanup_runs": 0,
        }

        # Start background cache cleanup
        self._start_cache_cleanup_timer()

    def _init_cosmos_service(self):
        """Initialize CosmosDB service with error handling."""
        try:
            self.cosmos_service = CosmosDBService()
            if self.cosmos_service.is_available():
                self.services_available["cosmos"] = True
                print("✅ CosmosDB service ready")
            else:
                print("⚠️  CosmosDB service not available")
        except Exception as e:
            print(f"❌ Failed to initialize CosmosDB service: {e}")
            self.cosmos_service = None

    def _init_search_service(self):
        """Initialize Azure Search service with error handling."""
        try:
            self.search_service = AzureSearchService()
            self.services_available["search"] = True
            print("✅ Azure Search service ready")
        except Exception as e:
            print(f"❌ Failed to initialize Azure Search service: {e}")
            self.search_service = None

    def _init_ai_project_client(self):
        """Initialize AI Project client with error handling."""
        try:
            self.ai_project_client = AIProjectClient(
                credential=DefaultAzureCredential(), endpoint=config.AZURE_AI_ENDPOINT
            )
            self.services_available["ai_project"] = True
            print("✅ AI Project client ready")
        except Exception as e:
            print(f"❌ Failed to initialize AI Project client: {e}")
            self.ai_project_client = None

    def _init_blob_service(self):
        """Initialize Blob storage service with error handling."""
        try:
            if config.STORAGE_CONNECTION_STRING:
                self.blob_service = BlobServiceClient.from_connection_string(
                    config.STORAGE_CONNECTION_STRING
                )
                self._ensure_storage_container()
                self.services_available["blob_storage"] = True
                print("✅ Blob storage service ready")
            else:
                print("⚠️  Blob storage connection string not configured")
        except Exception as e:
            print(f"❌ Failed to initialize Blob storage service: {e}")
            self.blob_service = None

    def _init_agent(self):
        """Initialize AI agent with error handling."""
        try:
            if self.ai_project_client:
                self.agent = self._get_or_create_agent()
                if self.agent:
                    self.services_available["agent"] = True
                    print("✅ AI agent ready")
            else:
                print("⚠️  AI agent not available (AI Project client not initialized)")
        except Exception as e:
            print(f"❌ Failed to initialize AI agent: {e}")
            self.agent = None

    def _ensure_storage_container(self):
        """Ensure the storage container exists."""
        try:
            container_client = self.blob_service.get_container_client(
                config.STORAGE_CONTAINER_NAME
            )
            if not container_client.exists():
                container_client.create_container()
                print(f"Created storage container: {config.STORAGE_CONTAINER_NAME}")
        except Exception as e:
            print(f"Error ensuring storage container: {e}")

    def _get_or_create_agent(self):
        """Get existing agent or create a new one."""
        try:
            from azure.ai.agents.models import (
                ListSortOrder,
                CodeInterpreterTool,
                ToolResources,
                CodeInterpreterToolResource,
            )
            from invoice_instructions import get_invoice_instructions

            # Try to get existing agent
            if config.AGENT_ID:
                try:
                    agent = self.ai_project_client.agents.get_agent(config.AGENT_ID)
                    print(f"Using existing agent: {agent.id}")
                    return agent
                except:
                    print("Existing agent not found, creating new one...")

            # Create new agent
            agent_instructions = get_invoice_instructions().format(
                company_name=config.COMPANY_NAME,
                company_address=config.COMPANY_ADDRESS,
                company_phone=config.COMPANY_PHONE,
                company_email=config.COMPANY_EMAIL,
                company_website=config.COMPANY_WEBSITE,
                company_tax_id=config.COMPANY_TAX_ID,
            )

            code_interpreter_tool = CodeInterpreterTool()
            tool_resources = ToolResources(
                code_interpreter=CodeInterpreterToolResource(file_ids=[])
            )

            agent = self.ai_project_client.agents.create_agent(
                model="gpt-4o",
                name="invoice-agent",
                description="Professional invoice generation agent",
                instructions=agent_instructions,
                tools=[code_interpreter_tool],
                tool_resources=tool_resources,
                temperature=0.1,
                metadata={
                    "purpose": "invoice_generation",
                    "version": "1.0",
                    "created_by": "service_manager",
                },
            )

            print(f"Created new agent: {agent.id}")
            return agent

        except Exception as e:
            print(f"Error creating agent: {e}")
            return None

    # Advanced Caching methods
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid with enhanced validation."""
        if cache_key not in self.cache_timestamps:
            return False

        cache_type = cache_key.split("_")[0]
        ttl = self.cache_ttl.get(cache_type, 300)  # Default 5 minutes
        age = datetime.now().timestamp() - self.cache_timestamps[cache_key]
        return age < ttl

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache with LRU tracking and statistics."""
        self.cache_stats["total_requests"] += 1

        if self._is_cache_valid(cache_key):
            # Update access tracking for LRU
            self.cache_access_count[cache_key] = (
                self.cache_access_count.get(cache_key, 0) + 1
            )
            self.cache_hit_count[cache_key] = self.cache_hit_count.get(cache_key, 0) + 1
            self.cache_stats["cache_hits"] += 1

            # Update timestamp for LRU (most recently accessed)
            self.cache_timestamps[cache_key] = datetime.now().timestamp()

            return self.cache.get(cache_key)

        # Cache miss
        self.cache_miss_count[cache_key] = self.cache_miss_count.get(cache_key, 0) + 1
        self.cache_stats["cache_misses"] += 1
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """Set data in cache with LRU eviction and size management."""
        cache_type = cache_key.split("_")[0]
        max_size = self.cache_max_size.get(cache_type, 50)

        # Check if we need to evict items for this cache type
        current_items = [key for key in self.cache.keys() if key.startswith(cache_type)]

        if len(current_items) >= max_size:
            self._evict_lru_items(cache_type, len(current_items) - max_size + 1)

        # Set the new cache entry
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now().timestamp()
        self.cache_access_count[cache_key] = 1
        self.cache_hit_count[cache_key] = 0
        self.cache_miss_count[cache_key] = 0

    def _evict_lru_items(self, cache_type: str, count: int):
        """Evict least recently used items for a specific cache type."""
        # Get all items of this cache type
        type_items = [
            (key, self.cache_timestamps[key])
            for key in self.cache.keys()
            if key.startswith(cache_type)
        ]

        # Sort by timestamp (oldest first)
        type_items.sort(key=lambda x: x[1])

        # Evict the oldest items
        for i in range(min(count, len(type_items))):
            key_to_evict = type_items[i][0]
            self._remove_cache_entry(key_to_evict)
            self.cache_stats["evictions"] += 1

    def _remove_cache_entry(self, cache_key: str):
        """Remove a cache entry and all its tracking data."""
        self.cache.pop(cache_key, None)
        self.cache_timestamps.pop(cache_key, None)
        self.cache_access_count.pop(cache_key, None)
        self.cache_hit_count.pop(cache_key, None)
        self.cache_miss_count.pop(cache_key, None)

    def _clear_cache(self, pattern: str = None):
        """Clear cache entries with enhanced pattern matching and statistics."""
        if pattern:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._remove_cache_entry(key)
        else:
            # Clear all caches
            self.cache.clear()
            self.cache_timestamps.clear()
            self.cache_access_count.clear()
            self.cache_hit_count.clear()
            self.cache_miss_count.clear()

    def _start_cache_cleanup_timer(self):
        """Start background timer for automatic cache cleanup."""
        import threading

        def cleanup_expired_cache():
            """Clean up expired cache entries."""
            try:
                current_time = datetime.now().timestamp()
                expired_keys = []

                for cache_key, timestamp in self.cache_timestamps.items():
                    cache_type = cache_key.split("_")[0]
                    ttl = self.cache_ttl.get(cache_type, 300)

                    if current_time - timestamp > ttl:
                        expired_keys.append(cache_key)

                # Remove expired entries
                for key in expired_keys:
                    self._remove_cache_entry(key)

                if expired_keys:
                    print(
                        f"🧹 Cache cleanup: removed {len(expired_keys)} expired entries"
                    )

                self.cache_stats["cleanup_runs"] += 1

                # Schedule next cleanup in 5 minutes
                timer = threading.Timer(300, cleanup_expired_cache)
                timer.daemon = True
                timer.start()

            except Exception as e:
                print(f"Cache cleanup error: {e}")

        # Start the first cleanup timer
        timer = threading.Timer(300, cleanup_expired_cache)  # 5 minutes
        timer.daemon = True
        timer.start()

    def get_cache_statistics(self) -> Dict:
        """Get comprehensive cache performance statistics."""
        total_requests = self.cache_stats["total_requests"]
        hit_rate = (
            (self.cache_stats["cache_hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        # Calculate cache sizes by type
        cache_sizes = {}
        for cache_type in self.cache_ttl.keys():
            cache_sizes[cache_type] = len(
                [key for key in self.cache.keys() if key.startswith(cache_type)]
            )

        return {
            "performance": {
                "total_requests": total_requests,
                "cache_hits": self.cache_stats["cache_hits"],
                "cache_misses": self.cache_stats["cache_misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self.cache_stats["evictions"],
                "cleanup_runs": self.cache_stats["cleanup_runs"],
            },
            "cache_sizes": cache_sizes,
            "total_cached_items": len(self.cache),
            "memory_usage": {
                "cache_entries": len(self.cache),
                "timestamp_entries": len(self.cache_timestamps),
                "access_count_entries": len(self.cache_access_count),
            },
        }

    # Enhanced Service access methods with advanced caching
    def get_statistics(self, force_refresh: bool = False) -> Dict:
        """Get invoice statistics with enhanced caching."""
        cache_key = "statistics_main"

        if not force_refresh:
            cached_stats = self._get_from_cache(cache_key)
            if cached_stats:
                print("📊 Using cached statistics")
                return cached_stats

        if not self.services_available["cosmos"] or not self.cosmos_service:
            return {
                "total_invoices": 0,
                "status_breakdown": [],
                "total_outstanding_amount": 0.0,
                "error": "CosmosDB service not available",
            }

        print("🔄 Calculating fresh statistics...")
        stats = self.cosmos_service.get_invoice_statistics()
        self._set_cache(cache_key, stats)
        return stats

    def generate_invoice(self, order_details: Dict) -> Dict:
        """Generate invoice with enhanced AI reliability."""
        from generate_invoices import InvoiceGenerationSystem

        # Use the enhanced generation system
        generator = InvoiceGenerationSystem()
        return generator.generate_invoice(order_details)

    @property
    def enhanced_ai_generate(self):
        """Get AI generation method with retry logic."""
        return self.rate_limit_handler.with_retry(
            max_retries=5, base_delay=2.0, max_delay=120.0
        )(self._ai_generate_with_fallback)

    def _ai_generate_with_fallback(self, prompt: str, context: Dict = None) -> Dict:
        """AI generation with intelligent fallback."""
        try:
            # Check AI service availability
            if not self.is_service_available(
                "ai_project"
            ) or not self.is_service_available("agent"):
                raise Exception("AI services not available")

            ai_client = self.get_ai_project_client()
            agent = self.get_agent()

            if not ai_client or not agent:
                raise Exception("AI client or agent not properly initialized")

            # Create thread with timeout
            thread = ai_client.agents.threads.create()

            # Send message
            message = ai_client.agents.messages.create(
                thread_id=thread.id, role="user", content=prompt
            )

            # Run agent with timeout
            run = ai_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id,
                instructions="Process the request and provide a comprehensive response.",
            )

            if run.status == "completed":
                # Get response
                from azure.ai.agents.models import ListSortOrder

                messages = ai_client.agents.messages.list(
                    thread_id=thread.id, order=ListSortOrder.ASCENDING
                )

                # Extract AI response
                assistant_messages = [
                    msg for msg in messages if msg.role == "assistant"
                ]
                if assistant_messages:
                    last_message = assistant_messages[-1]
                    if last_message.text_messages:
                        response = last_message.text_messages[-1].text.value
                        return {
                            "success": True,
                            "response": response,
                            "thread_id": thread.id,
                            "method": "ai_generated",
                        }

            elif run.status == "failed":
                error_msg = f"AI processing failed: {run.last_error}"
                raise Exception(error_msg)

            raise Exception("AI processing did not complete successfully")

        except Exception as e:
            # Log the error for monitoring
            print(f"AI generation failed: {str(e)}")
            raise e

    def list_invoices(self, limit: int = 50, force_refresh: bool = False) -> List[Dict]:
        """List invoices with enhanced caching and query optimization."""
        cache_key = f"invoice_list_{limit}"

        if not force_refresh:
            cached_list = self._get_from_cache(cache_key)
            if cached_list:
                print(f"📋 Using cached invoice list ({len(cached_list)} items)")
                return cached_list

        if not self.services_available["cosmos"] or not self.cosmos_service:
            return []

        print(f"🔄 Fetching fresh invoice list (limit: {limit})...")
        invoices = self.cosmos_service.list_invoices(limit)
        self._set_cache(cache_key, invoices)
        return invoices

    def search_invoices(self, query: str, force_refresh: bool = False) -> List[Dict]:
        """Search invoices with enhanced caching and fallback optimization."""
        # Create cache key based on query hash for better cache management
        import hashlib

        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        cache_key = f"search_results_{query_hash}"

        if not force_refresh:
            cached_results = self._get_from_cache(cache_key)
            if cached_results:
                print(f"🔍 Using cached search results for '{query}'")
                return cached_results

        results = []

        # Try Azure Search first with error handling
        if self.services_available["search"] and self.search_service:
            try:
                results = self.search_service.search_invoices(query)
                print(f"🔍 Azure Search found {len(results)} results for '{query}'")
            except Exception as e:
                print(f"Azure Search failed: {e}")

        # Fallback to CosmosDB search if Azure Search failed or returned no results
        if not results and self.services_available["cosmos"] and self.cosmos_service:
            try:
                results = self.cosmos_service.search_invoices(query)
                print(f"🔍 CosmosDB search found {len(results)} results for '{query}'")
            except Exception as e:
                print(f"CosmosDB search failed: {e}")

        # Cache results even if empty (to avoid repeated failed searches)
        self._set_cache(cache_key, results)
        return results

    def get_invoice(
        self, invoice_number: str, force_refresh: bool = False
    ) -> Optional[Dict]:
        """Get specific invoice with caching for better performance."""
        cache_key = f"invoice_detail_{invoice_number}"

        if not force_refresh:
            cached_invoice = self._get_from_cache(cache_key)
            if cached_invoice:
                print(f"📄 Using cached invoice: {invoice_number}")
                return cached_invoice

        if not self.services_available["cosmos"] or not self.cosmos_service:
            return None

        print(f"🔄 Fetching fresh invoice: {invoice_number}")
        invoice = self.cosmos_service.get_invoice(invoice_number)

        # Cache the result (even if None to avoid repeated lookups)
        self._set_cache(cache_key, invoice)
        return invoice

    def get_client_invoices(
        self, client_name: str, force_refresh: bool = False
    ) -> List[Dict]:
        """Get all invoices for a specific client with caching."""
        # Normalize client name for consistent caching
        client_key = client_name.lower().replace(" ", "_")
        cache_key = f"client_data_{client_key}"

        if not force_refresh:
            cached_invoices = self._get_from_cache(cache_key)
            if cached_invoices:
                print(f"👤 Using cached client invoices for: {client_name}")
                return cached_invoices

        # Search for invoices by client name
        invoices = self.search_invoices(client_name)

        # Filter to exact client matches
        client_invoices = []
        for invoice in invoices:
            invoice_data = invoice.get("invoice_data", {})
            invoice_client = invoice_data.get("client", {}).get("name", "")
            if invoice_client.lower() == client_name.lower():
                client_invoices.append(invoice)

        self._set_cache(cache_key, client_invoices)
        print(f"👤 Found {len(client_invoices)} invoices for client: {client_name}")
        return client_invoices

    def get_service_status_cached(self, force_refresh: bool = False) -> Dict:
        """Get service status with caching for dashboard performance."""
        cache_key = "service_status_main"

        if not force_refresh:
            cached_status = self._get_from_cache(cache_key)
            if cached_status:
                return cached_status

        status = self.get_service_status()

        # Add cache statistics to service status
        status["cache_statistics"] = self.get_cache_statistics()

        self._set_cache(cache_key, status)
        return status

    def save_invoice(self, invoice_data: Dict) -> Dict:
        """Save invoice and intelligently clear relevant caches."""
        result = {
            "cosmos_saved": False,
            "search_indexed": False,
            "storage_warnings": [],
        }

        # Save to CosmosDB
        if self.services_available["cosmos"] and self.cosmos_service:
            try:
                result["cosmos_saved"] = self.cosmos_service.save_invoice(invoice_data)
            except Exception as e:
                print(f"CosmosDB save failed: {e}")
                result["storage_warnings"].append("Failed to save to CosmosDB")

        # Index in Azure Search
        if self.services_available["search"] and self.search_service:
            try:
                result["search_indexed"] = self.search_service.index_invoice(
                    invoice_data, None
                )
            except Exception as e:
                print(f"Search indexing failed: {e}")
                result["storage_warnings"].append("Failed to index in Azure Search")

        # Intelligent cache invalidation
        if result["cosmos_saved"]:
            invoice_number = invoice_data.get("invoice_number")
            client_name = invoice_data.get("client", {}).get("name", "")

            # Clear specific caches that are now stale
            self._clear_cache("statistics")
            self._clear_cache("invoice_list")

            # Clear specific invoice cache if it exists
            if invoice_number:
                self._remove_cache_entry(f"invoice_detail_{invoice_number}")

            # Clear client cache if client name exists
            if client_name:
                client_key = client_name.lower().replace(" ", "_")
                self._remove_cache_entry(f"client_data_{client_key}")

            print("🗑️  Intelligently cleared relevant caches after save")

        return result

    def update_invoice_status(self, invoice_number: str, status: str) -> bool:
        """Update invoice status and clear relevant caches."""
        success = False

        # Update in CosmosDB
        if self.services_available["cosmos"] and self.cosmos_service:
            success = self.cosmos_service.update_invoice_status(invoice_number, status)

        # Update in Search
        if self.services_available["search"] and self.search_service:
            self.search_service.update_invoice_status_in_index(invoice_number, status)

        # Intelligent cache invalidation
        if success:
            # Clear caches that depend on invoice status
            self._clear_cache("statistics")  # Status affects statistics
            self._remove_cache_entry(
                f"invoice_detail_{invoice_number}"
            )  # Specific invoice changed

            # Clear search results that might include this invoice
            search_keys = [
                key for key in self.cache.keys() if key.startswith("search_results")
            ]
            for key in search_keys:
                self._remove_cache_entry(key)

            print("🗑️  Cleared relevant caches after status update")

        return success

    # Service availability checks
    def is_service_available(self, service_name: str) -> bool:
        """Check if a specific service is available with enhanced validation."""
        base_available = self.services_available.get(service_name, False)

        # For AI services, do additional validation
        if service_name == "ai_project" and base_available:
            return self.ai_project_client is not None
        elif service_name == "agent" and base_available:
            return self.agent is not None and self.ai_project_client is not None

        return base_available

    def test_ai_connectivity(self) -> Dict:
        """Test AI service connectivity and return detailed status."""
        status = {
            "ai_project_client": False,
            "agent_available": False,
            "can_create_thread": False,
            "can_send_message": False,
            "error": None,
        }

        try:
            # Test AI Project client
            if self.ai_project_client:
                status["ai_project_client"] = True

                # Test agent availability
                if self.agent:
                    status["agent_available"] = True

                    # Test thread creation
                    try:
                        test_thread = self.ai_project_client.agents.threads.create()
                        status["can_create_thread"] = True

                        # Test message sending
                        try:
                            self.ai_project_client.agents.messages.create(
                                thread_id=test_thread.id,
                                role="user",
                                content="Test connectivity",
                            )
                            status["can_send_message"] = True
                        except Exception as e:
                            status["error"] = f"Message test failed: {str(e)}"

                    except Exception as e:
                        status["error"] = f"Thread creation failed: {str(e)}"
                else:
                    status["error"] = "Agent not available"
            else:
                status["error"] = "AI Project client not available"

        except Exception as e:
            status["error"] = f"AI connectivity test failed: {str(e)}"

        return status

    def get_service_status(self) -> Dict:
        """Get status of all services with enhanced AI diagnostics."""
        base_status = {
            "services_available": self.services_available.copy(),
            "cache_stats": {
                "cached_items": len(self.cache),
                "cache_keys": list(self.cache.keys()),
            },
        }

        # Add AI connectivity test results
        if self.services_available.get("ai_project", False):
            base_status["ai_connectivity"] = self.test_ai_connectivity()

        return base_status

    # Direct service access (for advanced operations)
    def get_cosmos_service(self) -> Optional[CosmosDBService]:
        """Get direct access to CosmosDB service."""
        return self.cosmos_service if self.services_available["cosmos"] else None

    def get_search_service(self) -> Optional[AzureSearchService]:
        """Get direct access to Azure Search service."""
        return self.search_service if self.services_available["search"] else None

    def get_ai_project_client(self) -> Optional[AIProjectClient]:
        """Get direct access to AI Project client."""
        return self.ai_project_client if self.services_available["ai_project"] else None

    def get_agent(self):
        """Get direct access to AI agent."""
        return self.agent if self.services_available["agent"] else None

    def get_blob_service(self) -> Optional[BlobServiceClient]:
        """Get direct access to Blob service."""
        return self.blob_service if self.services_available["blob_storage"] else None


# Global service manager instance
_service_manager = None
_manager_lock = threading.Lock()


def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        with _manager_lock:
            if _service_manager is None:
                _service_manager = ServiceManager()
    return _service_manager


def reset_service_manager():
    """Reset the service manager (for testing purposes)."""
    global _service_manager
    with _manager_lock:
        _service_manager = None
        ServiceManager._instance = None
        ServiceManager._initialized = False
