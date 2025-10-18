"""
Performance Monitoring Service.

This service provides performance monitoring and metrics collection
for the VEA Connect application.
"""

import time
import logging
import psutil
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from django.conf import settings

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring service for tracking application metrics.
    
    Provides methods for tracking response times, resource usage,
    and application performance metrics.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = defaultdict(deque)
        self.max_metrics_history = 1000
        self.monitoring_enabled = True
        self.start_time = time.time()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _start_background_monitoring(self):
        """Start background monitoring thread."""
        if not self.monitoring_enabled:
            return
        
        def monitor_resources():
            while self.monitoring_enabled:
                try:
                    self._collect_system_metrics()
                    time.sleep(60)  # Collect every minute
                except Exception as e:
                    logger.error(f"Error in background monitoring: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
        monitor_thread.start()
        logger.info("Background performance monitoring started")
    
    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system.cpu_percent', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric('system.memory_percent', memory.percent)
            self.record_metric('system.memory_available_mb', memory.available / 1024 / 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric('system.disk_percent', disk.percent)
            
            # Network I/O
            network = psutil.net_io_counters()
            self.record_metric('system.network_bytes_sent', network.bytes_sent)
            self.record_metric('system.network_bytes_recv', network.bytes_recv)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
        """
        if not self.monitoring_enabled:
            return
        
        try:
            timestamp = datetime.utcnow()
            metric_data = {
                'timestamp': timestamp,
                'value': value,
                'tags': tags or {}
            }
            
            self.metrics[name].append(metric_data)
            
            # Keep only recent metrics
            if len(self.metrics[name]) > self.max_metrics_history:
                self.metrics[name].popleft()
                
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
    
    def record_response_time(self, endpoint: str, method: str, duration_ms: float, status_code: int):
        """
        Record HTTP response time.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            duration_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        tags = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        }
        
        self.record_metric('http.response_time_ms', duration_ms, tags)
        self.record_metric('http.requests_total', 1, tags)
        
        # Record success/failure
        success = 200 <= status_code < 400
        success_tags = tags.copy()
        success_tags['success'] = str(success)
        self.record_metric('http.requests_success', 1 if success else 0, success_tags)
    
    def record_whatsapp_metric(self, operation: str, duration_ms: float, success: bool, phone_number: str = None):
        """
        Record WhatsApp operation metrics.
        
        Args:
            operation: Operation type (send_message, receive_message, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            phone_number: Phone number (optional, for privacy)
        """
        tags = {
            'operation': operation,
            'success': str(success)
        }
        
        if phone_number:
            # Hash phone number for privacy
            import hashlib
            phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:8]
            tags['phone_hash'] = phone_hash
        
        self.record_metric('whatsapp.operation_duration_ms', duration_ms, tags)
        self.record_metric('whatsapp.operations_total', 1, tags)
        self.record_metric('whatsapp.operations_success', 1 if success else 0, tags)
    
    def record_cache_metric(self, operation: str, duration_ms: float, success: bool, cache_type: str = 'redis'):
        """
        Record cache operation metrics.
        
        Args:
            operation: Cache operation (get, set, delete, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            cache_type: Type of cache (redis, memory, etc.)
        """
        tags = {
            'operation': operation,
            'cache_type': cache_type,
            'success': str(success)
        }
        
        self.record_metric('cache.operation_duration_ms', duration_ms, tags)
        self.record_metric('cache.operations_total', 1, tags)
        self.record_metric('cache.operations_success', 1 if success else 0, tags)
    
    def record_database_metric(self, operation: str, duration_ms: float, success: bool, table: str = None):
        """
        Record database operation metrics.
        
        Args:
            operation: Database operation (select, insert, update, delete)
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            table: Database table name (optional)
        """
        tags = {
            'operation': operation,
            'success': str(success)
        }
        
        if table:
            tags['table'] = table
        
        self.record_metric('database.operation_duration_ms', duration_ms, tags)
        self.record_metric('database.operations_total', 1, tags)
        self.record_metric('database.operations_success', 1 if success else 0, tags)
    
    def get_metric_stats(self, name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get statistics for a metric over a time window.
        
        Args:
            name: Metric name
            window_minutes: Time window in minutes
            
        Returns:
            Dictionary with metric statistics
        """
        try:
            if name not in self.metrics:
                return {}
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_metrics = [
                m for m in self.metrics[name]
                if m['timestamp'] >= cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            values = [m['value'] for m in recent_metrics]
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1] if values else None,
                'window_minutes': window_minutes
            }
            
        except Exception as e:
            logger.error(f"Error getting metric stats for {name}: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all performance metrics.
        
        Returns:
            Dictionary with performance summary
        """
        try:
            summary = {
                'uptime_seconds': time.time() - self.start_time,
                'metrics_count': len(self.metrics),
                'system': {},
                'http': {},
                'whatsapp': {},
                'cache': {},
                'database': {}
            }
            
            # System metrics
            system_metrics = ['system.cpu_percent', 'system.memory_percent', 'system.disk_percent']
            for metric in system_metrics:
                stats = self.get_metric_stats(metric, window_minutes=5)
                if stats:
                    summary['system'][metric] = stats
            
            # HTTP metrics
            http_stats = self.get_metric_stats('http.response_time_ms', window_minutes=60)
            if http_stats:
                summary['http']['response_time'] = http_stats
            
            # WhatsApp metrics
            whatsapp_stats = self.get_metric_stats('whatsapp.operation_duration_ms', window_minutes=60)
            if whatsapp_stats:
                summary['whatsapp']['operation_duration'] = whatsapp_stats
            
            # Cache metrics
            cache_stats = self.get_metric_stats('cache.operation_duration_ms', window_minutes=60)
            if cache_stats:
                summary['cache']['operation_duration'] = cache_stats
            
            # Database metrics
            db_stats = self.get_metric_stats('database.operation_duration_ms', window_minutes=60)
            if db_stats:
                summary['database']['operation_duration'] = db_stats
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get performance alerts based on thresholds.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        try:
            # CPU usage alert
            cpu_stats = self.get_metric_stats('system.cpu_percent', window_minutes=5)
            if cpu_stats and cpu_stats.get('avg', 0) > 80:
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'warning',
                    'message': f"High CPU usage: {cpu_stats['avg']:.1f}%",
                    'value': cpu_stats['avg'],
                    'threshold': 80
                })
            
            # Memory usage alert
            memory_stats = self.get_metric_stats('system.memory_percent', window_minutes=5)
            if memory_stats and memory_stats.get('avg', 0) > 85:
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'warning',
                    'message': f"High memory usage: {memory_stats['avg']:.1f}%",
                    'value': memory_stats['avg'],
                    'threshold': 85
                })
            
            # Disk usage alert
            disk_stats = self.get_metric_stats('system.disk_percent', window_minutes=5)
            if disk_stats and disk_stats.get('avg', 0) > 90:
                alerts.append({
                    'type': 'high_disk_usage',
                    'severity': 'critical',
                    'message': f"High disk usage: {disk_stats['avg']:.1f}%",
                    'value': disk_stats['avg'],
                    'threshold': 90
                })
            
            # HTTP response time alert
            http_stats = self.get_metric_stats('http.response_time_ms', window_minutes=10)
            if http_stats and http_stats.get('avg', 0) > 5000:  # 5 seconds
                alerts.append({
                    'type': 'slow_http_response',
                    'severity': 'warning',
                    'message': f"Slow HTTP response time: {http_stats['avg']:.0f}ms",
                    'value': http_stats['avg'],
                    'threshold': 5000
                })
            
            # WhatsApp operation alert
            whatsapp_stats = self.get_metric_stats('whatsapp.operation_duration_ms', window_minutes=10)
            if whatsapp_stats and whatsapp_stats.get('avg', 0) > 10000:  # 10 seconds
                alerts.append({
                    'type': 'slow_whatsapp_operation',
                    'severity': 'warning',
                    'message': f"Slow WhatsApp operation: {whatsapp_stats['avg']:.0f}ms",
                    'value': whatsapp_stats['avg'],
                    'threshold': 10000
                })
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
        
        return alerts
    
    def clear_old_metrics(self, hours: int = 24):
        """
        Clear metrics older than specified hours.
        
        Args:
            hours: Age threshold in hours
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            for metric_name in list(self.metrics.keys()):
                # Remove old metrics
                self.metrics[metric_name] = deque(
                    m for m in self.metrics[metric_name]
                    if m['timestamp'] >= cutoff_time
                )
                
                # Remove empty metrics
                if not self.metrics[metric_name]:
                    del self.metrics[metric_name]
            
            logger.info(f"Cleared metrics older than {hours} hours")
            
        except Exception as e:
            logger.error(f"Error clearing old metrics: {e}")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_enabled = False
        logger.info("Performance monitoring stopped")


# Global instance for easy access
performance_monitor = PerformanceMonitor()


# Decorator for tracking function performance
def track_performance(operation_name: str, category: str = 'custom'):
    """
    Decorator to track function performance.
    
    Args:
        operation_name: Name of the operation
        category: Category of the operation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                tags = {'operation': operation_name, 'category': category}
                performance_monitor.record_metric(f'{category}.operation_duration_ms', duration_ms, tags)
                performance_monitor.record_metric(f'{category}.operations_total', 1, tags)
                performance_monitor.record_metric(f'{category}.operations_success', 1 if success else 0, tags)
        
        return wrapper
    return decorator
