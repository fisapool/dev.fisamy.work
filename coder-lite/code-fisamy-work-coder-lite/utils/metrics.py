import time
import logging
from typing import Dict, Any, List
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point"""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """In-memory metrics collector with Prometheus export"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Configuration
        self.retention_hours = 24
        self.cleanup_interval = 3600  # 1 hour
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def record_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Record a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] += value
        
        # Also record as time series
        self.metrics[f"counter_{name}"].append(
            MetricPoint(value=float(value), timestamp=time.time(), labels=labels or {})
        )
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        
        # Also record as time series
        self.metrics[f"gauge_{name}"].append(
            MetricPoint(value=value, timestamp=time.time(), labels=labels or {})
        )
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        # Also record as time series
        self.metrics[f"histogram_{name}"].append(
            MetricPoint(value=value, timestamp=time.time(), labels=labels or {})
        )
    
    def record_timing(self, name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record timing metric (alias for histogram)"""
        self.record_histogram(f"{name}_duration_ms", duration_ms, labels)
    
    def record_provision_event(self, event_type: str, duration_ms: float, 
                             plan: str, error_msg: str = None):
        """Record provision-specific metrics"""
        labels = {"plan": plan, "event_type": event_type}
        
        # Record timing
        self.record_timing("provision", duration_ms, labels)
        
        # Record counter
        self.record_counter("provision_events", 1, labels)
        
        # Record error if present
        if error_msg:
            self.record_counter("provision_errors", 1, {"plan": plan, "error": error_msg})
        
        # Record success/failure
        if event_type == "provision_success":
            self.record_counter("provision_success", 1, {"plan": plan})
        elif event_type == "provision_failure":
            self.record_counter("provision_failure", 1, {"plan": plan})
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> int:
        """Get current counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get current gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self.histograms.get(key, [])
        
        if not values:
            return {"count": 0, "min": 0, "max": 0, "mean": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)]
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        now = time.time()
        cutoff = now - (self.retention_hours * 3600)
        
        # Filter recent metrics
        recent_metrics = {}
        for name, points in self.metrics.items():
            recent_points = [p for p in points if p.timestamp >= cutoff]
            if recent_points:
                recent_metrics[name] = recent_points
        
        return {
            "timestamp": now,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {name: self.get_histogram_stats(name) for name in self.histograms},
            "recent_metrics": {name: len(points) for name, points in recent_metrics.items()}
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            name, labels = self._parse_key(key)
            if labels:
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                lines.append(f'{name}{{{label_str}}} {value}')
            else:
                lines.append(f'{name} {value}')
        
        # Gauges
        for key, value in self.gauges.items():
            name, labels = self._parse_key(key)
            if labels:
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                lines.append(f'{name}{{{label_str}}} {value}')
            else:
                lines.append(f'{name} {value}')
        
        # Histograms
        for key in self.histograms:
            name, labels = self._parse_key(key)
            stats = self.get_histogram_stats(name, labels)
            
            if labels:
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                lines.append(f'{name}_count{{{label_str}}} {stats["count"]}')
                lines.append(f'{name}_sum{{{label_str}}} {stats["mean"] * stats["count"]}')
                lines.append(f'{name}_min{{{label_str}}} {stats["min"]}')
                lines.append(f'{name}_max{{{label_str}}} {stats["max"]}')
                lines.append(f'{name}_p50{{{label_str}}} {stats["p50"]}')
                lines.append(f'{name}_p95{{{label_str}}} {stats["p95"]}')
                lines.append(f'{name}_p99{{{label_str}}} {stats["p99"]}')
            else:
                lines.append(f'{name}_count {stats["count"]}')
                lines.append(f'{name}_sum {stats["mean"] * stats["count"]}')
                lines.append(f'{name}_min {stats["min"]}')
                lines.append(f'{name}_max {stats["max"]}')
                lines.append(f'{name}_p50 {stats["p50"]}')
                lines.append(f'{name}_p95 {stats["p95"]}')
                lines.append(f'{name}_p99 {stats["p99"]}')
        
        return "\n".join(lines)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create key for metric storage"""
        if not labels:
            return name
        
        # Sort labels for consistent key generation
        sorted_labels = sorted(labels.items())
        label_str = ",".join([f"{k}={v}" for k, v in sorted_labels])
        return f"{name}:{label_str}"
    
    def _parse_key(self, key: str) -> tuple:
        """Parse key back to name and labels"""
        if ":" not in key:
            return key, {}
        
        name, label_str = key.split(":", 1)
        labels = {}
        
        for pair in label_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        
        return name, labels
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        import threading
        
        def cleanup_loop():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_old_metrics()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_metrics(self):
        """Remove old metrics outside retention window"""
        cutoff = time.time() - (self.retention_hours * 3600)
        
        for name, points in self.metrics.items():
            # Remove old points
            self.metrics[name] = deque(
                [p for p in points if p.timestamp >= cutoff],
                maxlen=1000
            )
        
        logger.debug("Cleaned up old metrics")

# Global metrics instance
metrics = MetricsCollector()

# Convenience functions
def record_provision_success(duration_ms: float, plan: str):
    """Record successful provision"""
    metrics.record_provision_event("provision_success", duration_ms, plan)

def record_provision_failure(duration_ms: float, plan: str, error_msg: str):
    """Record failed provision"""
    metrics.record_provision_event("provision_failure", duration_ms, plan, error_msg)

def record_caddy_reload(duration_ms: float):
    """Record Caddy reload timing"""
    metrics.record_timing("caddy_reload", duration_ms)

def record_quota_applied(plan: str, disk_gib: int):
    """Record quota application"""
    metrics.record_gauge("quota_disk_gib", float(disk_gib), {"plan": plan})

def get_provision_stats() -> Dict[str, Any]:
    """Get provision-specific statistics"""
    return {
        "success_rate": _calculate_success_rate(),
        "avg_duration": _calculate_avg_duration(),
        "plan_breakdown": _get_plan_breakdown(),
        "error_summary": _get_error_summary()
    }

def _calculate_success_rate() -> float:
    """Calculate overall provision success rate"""
    total_success = metrics.get_counter("provision_success")
    total_failure = metrics.get_counter("provision_failure")
    total = total_success + total_failure
    
    return (total_success / total * 100) if total > 0 else 0.0

def _calculate_avg_duration() -> float:
    """Calculate average provision duration"""
    stats = metrics.get_histogram_stats("provision_duration_ms")
    return stats.get("mean", 0.0)

def _get_plan_breakdown() -> Dict[str, Dict[str, int]]:
    """Get provision breakdown by plan"""
    plans = ["DEV-BASIC-1M", "DEV-PLUS-1M", "DEV-GPU-1M"]
    breakdown = {}
    
    for plan in plans:
        success = metrics.get_counter("provision_success", {"plan": plan})
        failure = metrics.get_counter("provision_failure", {"plan": plan})
        breakdown[plan] = {"success": success, "failure": failure, "total": success + failure}
    
    return breakdown

def _get_error_summary() -> Dict[str, int]:
    """Get error count by type"""
    # This would need to be implemented based on your error categorization
    return {"unknown": 0}
