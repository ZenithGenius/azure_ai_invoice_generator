"""
Monitoring and Metrics System
============================

Provides comprehensive monitoring with Prometheus metrics, performance tracking,
and business intelligence metrics collection.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable
from dataclasses import dataclass, asdict
from functools import wraps

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        CollectorRegistry,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("⚠️ Prometheus client not available - metrics collection will be limited")


@dataclass
class MetricEvent:
    """Represents a metric event."""

    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    metric_type: str  # counter, gauge, histogram, summary

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type,
        }


class MetricsCollector:
    """Collects and manages application metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self.metrics = {}
        self.custom_metrics = []
        self.callbacks: List[Callable] = []

        # Initialize core metrics
        self._initialize_core_metrics()

        # Performance tracking
        self.performance_data = {
            "request_times": [],
            "error_counts": {},
            "cache_stats": {},
            "system_stats": {},
        }

        # Background collection
        self.collection_thread = None
        self.is_collecting = False

    def _initialize_core_metrics(self):
        """Initialize core application metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Invoice generation metrics
        self.metrics["invoice_generation_total"] = Counter(
            "invoice_generation_total",
            "Total number of invoice generation attempts",
            ["status", "method"],
            registry=self.registry,
        )

        self.metrics["invoice_generation_duration"] = Histogram(
            "invoice_generation_duration_seconds",
            "Time spent generating invoices",
            ["method", "status"],
            registry=self.registry,
        )

        # Queue metrics
        self.metrics["queue_size"] = Gauge(
            "invoice_queue_size",
            "Current size of invoice generation queue",
            registry=self.registry,
        )

        self.metrics["queue_processing_time"] = Histogram(
            "queue_processing_time_seconds",
            "Time spent processing queue jobs",
            ["status"],
            registry=self.registry,
        )

        # Cache metrics
        self.metrics["cache_hits_total"] = Counter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_type"],
            registry=self.registry,
        )

        self.metrics["cache_misses_total"] = Counter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_type"],
            registry=self.registry,
        )

        # Service health metrics
        self.metrics["service_availability"] = Gauge(
            "service_availability",
            "Service availability status (1=available, 0=unavailable)",
            ["service_name"],
            registry=self.registry,
        )

        # Business metrics
        self.metrics["revenue_total"] = Gauge(
            "revenue_total",
            "Total revenue amount",
            ["currency"],
            registry=self.registry,
        )

        self.metrics["invoices_outstanding"] = Gauge(
            "invoices_outstanding",
            "Number of outstanding invoices",
            registry=self.registry,
        )

        # User activity metrics
        self.metrics["active_users"] = Gauge(
            "active_users", "Number of active users", registry=self.registry
        )

        self.metrics["page_views_total"] = Counter(
            "page_views_total", "Total page views", ["page"], registry=self.registry
        )

    def record_invoice_generation(self, method: str, status: str, duration: float):
        """Record invoice generation metrics."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["invoice_generation_total"].labels(
                status=status, method=method
            ).inc()

            self.metrics["invoice_generation_duration"].labels(
                method=method, status=status
            ).observe(duration)

        # Store custom metric
        self.custom_metrics.append(
            MetricEvent(
                name="invoice_generation",
                value=duration,
                labels={"method": method, "status": status},
                timestamp=datetime.now(),
                metric_type="histogram",
            )
        )

        self._trigger_callbacks(
            "invoice_generation",
            {"method": method, "status": status, "duration": duration},
        )

    def record_queue_metrics(
        self,
        queue_size: int,
        processing_jobs: int,
        completed_jobs: int,
        failed_jobs: int,
    ):
        """Record queue-related metrics."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["queue_size"].set(queue_size)

        # Store performance data
        self.performance_data["system_stats"]["queue"] = {
            "size": queue_size,
            "processing": processing_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "timestamp": datetime.now().isoformat(),
        }

    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["cache_hits_total"].labels(cache_type=cache_type).inc()

        if cache_type not in self.performance_data["cache_stats"]:
            self.performance_data["cache_stats"][cache_type] = {"hits": 0, "misses": 0}

        self.performance_data["cache_stats"][cache_type]["hits"] += 1

    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["cache_misses_total"].labels(cache_type=cache_type).inc()

        if cache_type not in self.performance_data["cache_stats"]:
            self.performance_data["cache_stats"][cache_type] = {"hits": 0, "misses": 0}

        self.performance_data["cache_stats"][cache_type]["misses"] += 1

    def record_service_availability(self, service_name: str, is_available: bool):
        """Record service availability."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["service_availability"].labels(service_name=service_name).set(
                1 if is_available else 0
            )

    def record_business_metrics(self, revenue_data: Dict, outstanding_invoices: int):
        """Record business metrics."""
        if PROMETHEUS_AVAILABLE:
            for currency, amount in revenue_data.items():
                self.metrics["revenue_total"].labels(currency=currency).set(amount)

            self.metrics["invoices_outstanding"].set(outstanding_invoices)

    def record_user_activity(self, active_users: int, page: str = None):
        """Record user activity metrics."""
        if PROMETHEUS_AVAILABLE:
            self.metrics["active_users"].set(active_users)

            if page:
                self.metrics["page_views_total"].labels(page=page).inc()

    def time_function(self, metric_name: str, labels: Dict[str, str] = None):
        """Decorator to time function execution."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    raise
                finally:
                    duration = time.time() - start_time

                    # Record timing metric
                    metric_labels = labels or {}
                    metric_labels["status"] = status

                    self.custom_metrics.append(
                        MetricEvent(
                            name=metric_name,
                            value=duration,
                            labels=metric_labels,
                            timestamp=datetime.now(),
                            metric_type="histogram",
                        )
                    )

                    # Store in performance data
                    if metric_name not in self.performance_data["request_times"]:
                        self.performance_data["request_times"] = []

                    self.performance_data["request_times"].append(
                        {
                            "function": func.__name__,
                            "duration": duration,
                            "status": status,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Keep only last 1000 entries
                    if len(self.performance_data["request_times"]) > 1000:
                        self.performance_data["request_times"] = self.performance_data[
                            "request_times"
                        ][-1000:]

            return wrapper

        return decorator

    def add_callback(self, callback: Callable):
        """Add callback for metric events."""
        self.callbacks.append(callback)

    def _trigger_callbacks(self, metric_name: str, data: Dict):
        """Trigger registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(metric_name, data)
            except Exception as e:
                print(f"Error in metrics callback: {e}")

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        if not PROMETHEUS_AVAILABLE or not self.registry:
            return "# Prometheus not available\n"

        return generate_latest(self.registry).decode("utf-8")

    def get_performance_summary(self) -> Dict:
        """Get performance summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "cache_performance": {},
            "request_performance": {},
            "error_rates": {},
            "system_health": {},
        }

        # Cache performance
        for cache_type, stats in self.performance_data["cache_stats"].items():
            total_requests = stats["hits"] + stats["misses"]
            hit_rate = (
                (stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            )

            summary["cache_performance"][cache_type] = {
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests,
                "hits": stats["hits"],
                "misses": stats["misses"],
            }

        # Request performance
        recent_requests = [
            req
            for req in self.performance_data["request_times"]
            if datetime.fromisoformat(req["timestamp"])
            > datetime.now() - timedelta(minutes=5)
        ]

        if recent_requests:
            durations = [req["duration"] for req in recent_requests]
            summary["request_performance"] = {
                "avg_duration": round(sum(durations) / len(durations), 3),
                "max_duration": round(max(durations), 3),
                "min_duration": round(min(durations), 3),
                "total_requests": len(recent_requests),
            }

        # Error rates
        error_requests = [req for req in recent_requests if req["status"] == "error"]
        if recent_requests:
            error_rate = len(error_requests) / len(recent_requests) * 100
            summary["error_rates"]["last_5_minutes"] = round(error_rate, 2)

        # System health
        summary["system_health"] = self.performance_data.get("system_stats", {})

        return summary

    def start_background_collection(self, interval: int = 60):
        """Start background metrics collection."""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collection_thread = threading.Thread(
            target=self._collection_loop, args=(interval,), daemon=True
        )
        self.collection_thread.start()
        print(f"📊 Started background metrics collection (interval: {interval}s)")

    def stop_background_collection(self):
        """Stop background metrics collection."""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        print("🛑 Stopped background metrics collection")

    def _collection_loop(self, interval: int):
        """Background collection loop."""
        while self.is_collecting:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                print(f"Error in metrics collection: {e}")
                time.sleep(interval)

    def _collect_system_metrics(self):
        """Collect system-wide metrics."""
        try:
            # Collect service manager metrics
            from service_manager import get_service_manager

            service_manager = get_service_manager()

            # Service availability
            service_status = service_manager.get_service_status()
            for service, available in service_status.get(
                "services_available", {}
            ).items():
                self.record_service_availability(service, available)

            # Cache metrics
            cache_stats = service_manager.get_cache_statistics()
            for cache_type, stats in cache_stats.get("cache_sizes", {}).items():
                # Record cache size as a gauge
                if PROMETHEUS_AVAILABLE:
                    if f"cache_size_{cache_type}" not in self.metrics:
                        self.metrics[f"cache_size_{cache_type}"] = Gauge(
                            f"cache_size_{cache_type}",
                            f"Size of {cache_type} cache",
                            registry=self.registry,
                        )
                    self.metrics[f"cache_size_{cache_type}"].set(stats)

            # Business metrics
            try:
                business_stats = service_manager.get_statistics()

                # Revenue by currency (simplified)
                total_revenue = business_stats.get("total_outstanding_amount", 0)
                self.record_business_metrics({"USD": total_revenue}, 0)  # Simplified

                # Outstanding invoices
                outstanding = business_stats.get("total_invoices", 0)
                if PROMETHEUS_AVAILABLE:
                    self.metrics["invoices_outstanding"].set(outstanding)

            except Exception as e:
                print(f"Error collecting business metrics: {e}")

            # Queue metrics if available
            try:
                from components.invoice_queue import get_invoice_queue

                queue = get_invoice_queue()
                queue_stats = queue.get_queue_stats()

                self.record_queue_metrics(
                    queue_stats["queue_length"],
                    queue_stats["processing_jobs"],
                    queue_stats["completed_jobs"],
                    queue_stats["failed_jobs"],
                )
            except Exception:
                pass  # Queue not available

        except Exception as e:
            print(f"Error in system metrics collection: {e}")


class PerformanceMonitor:
    """Monitors application performance and provides insights."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize performance monitor."""
        self.metrics_collector = metrics_collector
        self.alerts = []
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "error_rate": 5.0,  # percentage
            "cache_hit_rate": 70.0,  # percentage
            "queue_size": 50,  # number of jobs
        }

    def check_performance_alerts(self) -> List[Dict]:
        """Check for performance issues and generate alerts."""
        alerts = []
        summary = self.metrics_collector.get_performance_summary()

        # Check response time
        request_perf = summary.get("request_performance", {})
        avg_duration = request_perf.get("avg_duration", 0)

        if avg_duration > self.thresholds["response_time"]:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": f"High average response time: {avg_duration:.2f}s",
                    "threshold": self.thresholds["response_time"],
                    "current_value": avg_duration,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check error rate
        error_rate = summary.get("error_rates", {}).get("last_5_minutes", 0)

        if error_rate > self.thresholds["error_rate"]:
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "critical" if error_rate > 10 else "warning",
                    "message": f"High error rate: {error_rate:.1f}%",
                    "threshold": self.thresholds["error_rate"],
                    "current_value": error_rate,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Check cache performance
        cache_perf = summary.get("cache_performance", {})
        for cache_type, stats in cache_perf.items():
            hit_rate = stats.get("hit_rate", 0)

            if hit_rate < self.thresholds["cache_hit_rate"]:
                alerts.append(
                    {
                        "type": "cache_performance",
                        "severity": "warning",
                        "message": f"Low cache hit rate for {cache_type}: {hit_rate:.1f}%",
                        "threshold": self.thresholds["cache_hit_rate"],
                        "current_value": hit_rate,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Check queue size
        system_health = summary.get("system_health", {})
        queue_stats = system_health.get("queue", {})
        queue_size = queue_stats.get("size", 0)

        if queue_size > self.thresholds["queue_size"]:
            alerts.append(
                {
                    "type": "queue_size",
                    "severity": "warning",
                    "message": f"Large queue size: {queue_size} jobs",
                    "threshold": self.thresholds["queue_size"],
                    "current_value": queue_size,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Store alerts
        self.alerts.extend(alerts)

        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [
            alert
            for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

        return alerts

    def get_health_score(self) -> Dict:
        """Calculate overall system health score."""
        summary = self.metrics_collector.get_performance_summary()

        scores = {
            "response_time": 100,
            "error_rate": 100,
            "cache_performance": 100,
            "system_availability": 100,
        }

        # Response time score
        avg_duration = summary.get("request_performance", {}).get("avg_duration", 0)
        if avg_duration > 0:
            scores["response_time"] = max(
                0, 100 - (avg_duration / self.thresholds["response_time"] * 50)
            )

        # Error rate score
        error_rate = summary.get("error_rates", {}).get("last_5_minutes", 0)
        scores["error_rate"] = max(
            0, 100 - (error_rate / self.thresholds["error_rate"] * 20)
        )

        # Cache performance score
        cache_perf = summary.get("cache_performance", {})
        if cache_perf:
            avg_hit_rate = sum(
                stats["hit_rate"] for stats in cache_perf.values()
            ) / len(cache_perf)
            scores["cache_performance"] = min(100, avg_hit_rate)

        # Overall health score
        overall_score = sum(scores.values()) / len(scores)

        return {
            "overall_score": round(overall_score, 1),
            "component_scores": scores,
            "status": self._get_health_status(overall_score),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_health_status(self, score: float) -> str:
        """Get health status based on score."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"


# Global instances
_metrics_collector = None
_performance_monitor = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector.start_background_collection()
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        metrics_collector = get_metrics_collector()
        _performance_monitor = PerformanceMonitor(metrics_collector)
    return _performance_monitor


def cleanup_monitoring():
    """Cleanup monitoring instances."""
    global _metrics_collector, _performance_monitor

    if _metrics_collector:
        _metrics_collector.stop_background_collection()
        _metrics_collector = None

    _performance_monitor = None
    print("🛑 Monitoring services cleaned up")
