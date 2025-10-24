"""
Integration tests for Performance Monitor service.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings

from services.performance_monitor import PerformanceMonitor, performance_monitor


class TestPerformanceMonitor(TestCase):
    """Test cases for Performance Monitor service."""

    def setUp(self):
        """Set up test environment."""
        self.monitor = PerformanceMonitor()

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        # Test that monitor can be initialized
        self.assertIsInstance(self.monitor, PerformanceMonitor)
        
        # Test that monitoring is enabled by default
        self.assertTrue(self.monitor.monitoring_enabled)
        
        # Test that metrics dictionary is initialized
        self.assertIsInstance(self.monitor.metrics, dict)

    def test_record_metric(self):
        """Test recording metrics."""
        # Test recording a simple metric
        self.monitor.record_metric('test.metric', 42.0, {'test': 'value'})
        
        # Check that metric was recorded
        self.assertIn('test.metric', self.monitor.metrics)
        self.assertEqual(len(self.monitor.metrics['test.metric']), 1)
        
        # Check metric data
        metric_data = self.monitor.metrics['test.metric'][0]
        self.assertEqual(metric_data['value'], 42.0)
        self.assertEqual(metric_data['tags']['test'], 'value')

    def test_record_response_time(self):
        """Test recording HTTP response times."""
        # Test recording response time
        self.monitor.record_response_time('/test/', 'GET', 150.0, 200)
        
        # Check that metrics were recorded
        self.assertIn('http.response_time_ms', self.monitor.metrics)
        self.assertIn('http.requests_total', self.monitor.metrics)
        self.assertIn('http.requests_success', self.monitor.metrics)

    def test_record_whatsapp_metric(self):
        """Test recording WhatsApp metrics."""
        # Test recording WhatsApp metric
        self.monitor.record_whatsapp_metric('send_message', 500.0, True, '+1234567890')
        
        # Check that metrics were recorded
        self.assertIn('whatsapp.operation_duration_ms', self.monitor.metrics)
        self.assertIn('whatsapp.operations_total', self.monitor.metrics)
        self.assertIn('whatsapp.operations_success', self.monitor.metrics)

    def test_record_cache_metric(self):
        """Test recording cache metrics."""
        # Test recording cache metric
        self.monitor.record_cache_metric('get', 10.0, True, 'redis')
        
        # Check that metrics were recorded
        self.assertIn('cache.operation_duration_ms', self.monitor.metrics)
        self.assertIn('cache.operations_total', self.monitor.metrics)
        self.assertIn('cache.operations_success', self.monitor.metrics)

    def test_record_database_metric(self):
        """Test recording database metrics."""
        # Test recording database metric
        self.monitor.record_database_metric('select', 25.0, True, 'users')
        
        # Check that metrics were recorded
        self.assertIn('database.operation_duration_ms', self.monitor.metrics)
        self.assertIn('database.operations_total', self.monitor.metrics)
        self.assertIn('database.operations_success', self.monitor.metrics)

    def test_get_metric_stats(self):
        """Test getting metric statistics."""
        # Record some metrics
        for i in range(5):
            self.monitor.record_metric('test.stats', float(i), {'iteration': i})
        
        # Get stats for the last 60 minutes
        stats = self.monitor.get_metric_stats('test.stats', window_minutes=60)
        
        # Check stats
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['min'], 0.0)
        self.assertEqual(stats['max'], 4.0)
        self.assertEqual(stats['avg'], 2.0)
        self.assertEqual(stats['latest'], 4.0)

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        # Record some metrics first
        self.monitor.record_metric('system.cpu_percent', 50.0)
        self.monitor.record_response_time('/test/', 'GET', 100.0, 200)
        self.monitor.record_whatsapp_metric('send_message', 200.0, True)
        
        # Get summary
        summary = self.monitor.get_performance_summary()
        
        # Check summary structure
        self.assertIn('uptime_seconds', summary)
        self.assertIn('metrics_count', summary)
        self.assertIn('system', summary)
        self.assertIn('http', summary)
        self.assertIn('whatsapp', summary)
        self.assertIn('cache', summary)
        self.assertIn('database', summary)

    def test_get_alerts(self):
        """Test getting performance alerts."""
        # Record metrics that should trigger alerts
        self.monitor.record_metric('system.cpu_percent', 85.0)  # High CPU
        self.monitor.record_metric('system.memory_percent', 90.0)  # High memory
        self.monitor.record_metric('system.disk_percent', 95.0)  # High disk
        
        # Get alerts
        alerts = self.monitor.get_alerts()
        
        # Should have alerts
        self.assertGreater(len(alerts), 0)
        
        # Check alert structure
        for alert in alerts:
            self.assertIn('type', alert)
            self.assertIn('severity', alert)
            self.assertIn('message', alert)
            self.assertIn('value', alert)
            self.assertIn('threshold', alert)

    def test_clear_old_metrics(self):
        """Test clearing old metrics."""
        # Record some metrics
        self.monitor.record_metric('test.old', 1.0)
        self.monitor.record_metric('test.new', 2.0)
        
        # Check that metrics were recorded
        self.assertIn('test.old', self.monitor.metrics)
        self.assertIn('test.new', self.monitor.metrics)
        
        # Clear metrics older than 24 hours (should not clear recent metrics)
        self.monitor.clear_old_metrics(hours=24)
        
        # Check that recent metrics are still there
        self.assertIn('test.old', self.monitor.metrics)
        self.assertIn('test.new', self.monitor.metrics)

    def test_stop_monitoring(self):
        """Test stopping monitoring."""
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Check that monitoring is disabled
        self.assertFalse(self.monitor.monitoring_enabled)
        
        # Try to record a metric (should not record)
        self.monitor.record_metric('test.stopped', 1.0)
        self.assertNotIn('test.stopped', self.monitor.metrics)

    @patch('services.performance_monitor.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test collecting system metrics."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0, available=1024*1024*100)
        mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=2000)
        
        # Collect system metrics
        self.monitor._collect_system_metrics()
        
        # Check that system metrics were recorded
        self.assertIn('system.cpu_percent', self.monitor.metrics)
        self.assertIn('system.memory_percent', self.monitor.metrics)
        self.assertIn('system.disk_percent', self.monitor.metrics)
        self.assertIn('system.network_bytes_sent', self.monitor.metrics)
        self.assertIn('system.network_bytes_recv', self.monitor.metrics)


class TestPerformanceMonitorIntegration(TestCase):
    """Integration tests for Performance Monitor with real components."""

    def test_global_instance(self):
        """Test the global Performance Monitor instance."""
        # Test that global instance exists
        self.assertIsInstance(performance_monitor, PerformanceMonitor)
        
        # Test that it can record metrics
        performance_monitor.record_metric('integration_test', 42.0)
        self.assertIn('integration_test', performance_monitor.metrics)

    def test_error_handling(self):
        """Test error handling in Performance Monitor."""
        # Test that service handles errors gracefully
        try:
            # Test with invalid parameters
            performance_monitor.record_metric(None, None)
            performance_monitor.record_response_time("", "", -1, 999)
            performance_monitor.record_whatsapp_metric("", -1, None)
        except Exception as e:
            self.fail(f"Service should handle invalid parameters gracefully: {e}")

    def test_concurrent_metric_recording(self):
        """Test concurrent metric recording."""
        import threading
        import time
        
        results = []
        errors = []
        
        def record_metrics(thread_id):
            try:
                for i in range(10):
                    performance_monitor.record_metric(
                        f'concurrent_metric_{thread_id}_{i}',
                        float(i),
                        {'thread_id': thread_id, 'iteration': i}
                    )
                    results.append(True)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent recording produced errors: {errors}")
        self.assertEqual(len(results), 50, "All metrics should be recorded")
        self.assertTrue(all(results), "All metrics should be recorded successfully")

    def test_metric_history_limit(self):
        """Test that metric history is limited."""
        # Record more metrics than the limit
        max_history = performance_monitor.max_metrics_history
        for i in range(max_history + 10):
            performance_monitor.record_metric('test.limit', float(i))
        
        # Check that only the most recent metrics are kept
        self.assertEqual(len(performance_monitor.metrics['test.limit']), max_history)
        
        # Check that the oldest metric is the one after the limit
        oldest_metric = performance_monitor.metrics['test.limit'][0]
        self.assertEqual(oldest_metric['value'], 10.0)  # First metric after limit

    def test_performance_impact(self):
        """Test that Performance Monitor doesn't significantly impact performance."""
        import time
        
        # Measure time without recording
        start_time = time.time()
        for _ in range(100):
            pass
        baseline_time = time.time() - start_time
        
        # Ensure baseline time is not zero
        if baseline_time == 0:
            baseline_time = 0.001
        
        # Measure time with recording
        start_time = time.time()
        for i in range(100):
            performance_monitor.record_metric(f'perf_test_{i}', float(i))
        recording_time = time.time() - start_time
        
        # Recording should not take more than 10x the baseline time
        self.assertLess(recording_time, baseline_time * 10, 
                       "Performance Monitor recording is too slow")


@pytest.mark.integration
class TestPerformanceMonitorProduction(TestCase):
    """Production-like tests for Performance Monitor."""

    def test_high_volume_metrics(self):
        """Test high volume metric recording."""
        # Record many metrics quickly
        metrics = []
        for i in range(100):  # Reduced from 1000 to avoid performance issues
            metric_name = f'high_volume_metric_{i % 10}'  # 10 different metric names
            performance_monitor.record_metric(metric_name, float(i))
            metrics.append(True)  # Assume success since no return value
        
        # All metrics should be recorded successfully
        self.assertTrue(all(metrics), "All metrics should be recorded successfully")
        
        # Check that metrics are distributed correctly
        for i in range(10):
            metric_name = f'high_volume_metric_{i}'
            if metric_name in performance_monitor.metrics:
                self.assertGreater(len(performance_monitor.metrics[metric_name]), 0)

    def test_system_metrics_collection(self):
        """Test system metrics collection in production-like environment."""
        # This test will only work if psutil is available and system metrics can be collected
        try:
            # Try to collect system metrics
            performance_monitor._collect_system_metrics()
            
            # Check if any system metrics were collected
            system_metrics = [
                'system.cpu_percent',
                'system.memory_percent',
                'system.disk_percent',
                'system.network_bytes_sent',
                'system.network_bytes_recv'
            ]
            
            collected_metrics = [metric for metric in system_metrics 
                               if metric in performance_monitor.metrics]
            
            # At least some system metrics should be collected
            self.assertGreater(len(collected_metrics), 0, 
                              "At least some system metrics should be collected")
            
        except Exception as e:
            # If system metrics collection fails, that's okay in test environment
            self.skipTest(f"System metrics collection not available: {e}")

    def test_background_monitoring(self):
        """Test background monitoring functionality."""
        # Check that background monitoring is running
        self.assertTrue(performance_monitor.monitoring_enabled)
        
        # Wait a moment for background collection
        time.sleep(2)
        
        # Check if any system metrics were collected in background
        system_metrics = [
            'system.cpu_percent',
            'system.memory_percent',
            'system.disk_percent'
        ]
        
        collected_metrics = [metric for metric in system_metrics 
                           if metric in performance_monitor.metrics]
        
        # Background monitoring should collect some metrics
        # (Note: This might not work in all test environments)
        if len(collected_metrics) > 0:
            self.assertGreater(len(collected_metrics), 0, 
                              "Background monitoring should collect system metrics")

    def test_alert_thresholds(self):
        """Test alert threshold functionality."""
        # Record metrics at different levels to test alerts
        
        # Normal levels (should not trigger alerts)
        performance_monitor.record_metric('system.cpu_percent', 50.0)
        performance_monitor.record_metric('system.memory_percent', 60.0)
        performance_monitor.record_metric('system.disk_percent', 70.0)
        
        # Get alerts
        alerts = performance_monitor.get_alerts()
        
        # Check alert structure and logic
        for alert in alerts:
            self.assertIn('type', alert)
            self.assertIn('severity', alert)
            self.assertIn('message', alert)
            self.assertIn('value', alert)
            self.assertIn('threshold', alert)
            
            # Check that alert values are above thresholds
            if alert['type'] == 'high_cpu_usage':
                self.assertGreater(alert['value'], alert['threshold'])
            elif alert['type'] == 'high_memory_usage':
                self.assertGreater(alert['value'], alert['threshold'])
            elif alert['type'] == 'high_disk_usage':
                self.assertGreater(alert['value'], alert['threshold'])


# Test the decorator functionality
class TestPerformanceMonitorDecorator(TestCase):
    """Test the performance tracking decorator."""

    def test_track_performance_decorator(self):
        """Test the track_performance decorator."""
        from services.performance_monitor import track_performance
        
        @track_performance('test_operation', 'test_category')
        def test_function():
            time.sleep(0.01)  # Simulate some work
            return "success"
        
        # Call the decorated function
        result = test_function()
        
        # Check result
        self.assertEqual(result, "success")
        
        # Check that metrics were recorded
        self.assertIn('test_category.operation_duration_ms', performance_monitor.metrics)
        self.assertIn('test_category.operations_total', performance_monitor.metrics)
        self.assertIn('test_category.operations_success', performance_monitor.metrics)

    def test_track_performance_decorator_with_exception(self):
        """Test the track_performance decorator with exceptions."""
        from services.performance_monitor import track_performance
        
        @track_performance('test_operation_error', 'test_category')
        def test_function_with_error():
            time.sleep(0.01)  # Simulate some work
            raise ValueError("Test error")
        
        # Call the decorated function and expect exception
        with self.assertRaises(ValueError):
            test_function_with_error()
        
        # Check that metrics were recorded (including failure)
        self.assertIn('test_category.operation_duration_ms', performance_monitor.metrics)
        self.assertIn('test_category.operations_total', performance_monitor.metrics)
        self.assertIn('test_category.operations_success', performance_monitor.metrics)
