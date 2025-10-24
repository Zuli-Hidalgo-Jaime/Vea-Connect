"""
Integration tests for Application Insights service.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings

from services.application_insights import ApplicationInsightsService, app_insights


class TestApplicationInsightsService(TestCase):
    """Test cases for Application Insights service."""

    def setUp(self):
        """Set up test environment."""
        self.service = ApplicationInsightsService()

    def test_service_initialization(self):
        """Test service initialization."""
        # Test that service can be initialized
        self.assertIsInstance(self.service, ApplicationInsightsService)
        
        # Test configuration status
        status = self.service.get_configuration_status()
        self.assertIsInstance(status, dict)
        self.assertIn('enabled', status)
        self.assertIn('connection_string_configured', status)
        self.assertIn('instrumentation_key_configured', status)
        self.assertIn('opencensus_available', status)

    def test_track_event_without_connection_string(self):
        """Test tracking events when Application Insights is not configured."""
        # Test tracking event without connection string
        result = self.service.track_event(
            name="test_event",
            properties={"test": "value"},
            measurements={"duration": 100.0}
        )
        
        # Should return True (fallback to local logging)
        self.assertTrue(result)

    def test_track_exception_without_connection_string(self):
        """Test tracking exceptions when Application Insights is not configured."""
        # Test tracking exception without connection string
        test_exception = ValueError("Test exception")
        result = self.service.track_exception(
            exception=test_exception,
            properties={"test": "value"}
        )
        
        # Should return True (fallback to local logging)
        self.assertTrue(result)

    def test_track_metric_without_connection_string(self):
        """Test tracking metrics when Application Insights is not configured."""
        # Test tracking metric without connection string
        result = self.service.track_metric(
            name="test_metric",
            value=42.0,
            properties={"test": "value"}
        )
        
        # Should return True (fallback to local logging)
        self.assertTrue(result)

    def test_track_dependency_without_connection_string(self):
        """Test tracking dependencies when Application Insights is not configured."""
        # Test tracking dependency without connection string
        result = self.service.track_dependency(
            name="test_dependency",
            dependency_type="HTTP",
            target="https://api.example.com",
            duration_ms=150.0,
            success=True,
            properties={"test": "value"}
        )
        
        # Should return True (fallback to local logging)
        self.assertTrue(result)

    def test_track_request_without_connection_string(self):
        """Test tracking requests when Application Insights is not configured."""
        # Test tracking request without connection string
        result = self.service.track_request(
            name="test_request",
            url="https://api.example.com/test",
            method="GET",
            duration_ms=200.0,
            status_code=200,
            success=True,
            properties={"test": "value"}
        )
        
        # Should return True (fallback to local logging)
        self.assertTrue(result)

    def test_track_whatsapp_message(self):
        """Test tracking WhatsApp messages."""
        # Test tracking WhatsApp message
        result = self.service.track_whatsapp_message(
            phone_number="+1234567890",
            message_type="text",
            success=True,
            duration_ms=500.0,
            properties={"test": "value"}
        )
        
        # Should return True
        self.assertTrue(result)

    def test_track_whatsapp_message_with_error(self):
        """Test tracking WhatsApp messages with error."""
        # Test tracking WhatsApp message with error
        result = self.service.track_whatsapp_message(
            phone_number="+1234567890",
            message_type="text",
            success=False,
            duration_ms=1000.0,
            error_message="Test error",
            properties={"test": "value"}
        )
        
        # Should return True
        self.assertTrue(result)

    @patch('opencensus.ext.azure.log_exporter.AzureLogHandler')
    @patch('opencensus.ext.azure.trace_exporter.AzureExporter')
    @patch('opencensus.trace.tracer.Tracer')
    def test_service_with_mocked_application_insights(self, mock_tracer, mock_exporter, mock_handler):
        """Test service with mocked Application Insights components."""
        # Mock the Application Insights components
        mock_handler.return_value = MagicMock()
        mock_exporter.return_value = MagicMock()
        mock_tracer.return_value = MagicMock()
        
        # Create service with connection string
        with patch.dict('os.environ', {'APPLICATIONINSIGHTS_CONNECTION_STRING': 'test_connection_string'}):
            # Recreate service to pick up new environment variable
            service = ApplicationInsightsService()
            
            # Test that service is enabled
            status = service.get_configuration_status()
            self.assertTrue(status['enabled'])
            self.assertTrue(status['connection_string_configured'])

    def test_extract_instrumentation_key(self):
        """Test extraction of instrumentation key from connection string."""
        # Test with valid connection string
        test_connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.object(self.service, 'connection_string', test_connection_string):
            key = self.service._extract_instrumentation_key()
            self.assertEqual(key, 'test-key')
        
        # Test with invalid connection string
        with patch.object(self.service, 'connection_string', 'invalid_string'):
            key = self.service._extract_instrumentation_key()
            self.assertIsNone(key)
        
        # Test with no connection string
        with patch.object(self.service, 'connection_string', None):
            key = self.service._extract_instrumentation_key()
            self.assertIsNone(key)

    def test_get_setting_fallback(self):
        """Test setting retrieval with fallback to environment variables."""
        # Test with environment variable fallback
        with patch.dict('os.environ', {'TEST_SETTING': 'env_value'}):
            value = self.service._get_setting('TEST_SETTING')
            self.assertEqual(value, 'env_value')
        
        # Test with no setting available
        value = self.service._get_setting('NONEXISTENT_SETTING')
        self.assertIsNone(value)


class TestApplicationInsightsIntegration(TestCase):
    """Integration tests for Application Insights with real components."""

    def test_global_instance(self):
        """Test the global Application Insights instance."""
        # Test that global instance exists
        self.assertIsInstance(app_insights, ApplicationInsightsService)
        
        # Test that it can track events
        result = app_insights.track_event("integration_test", {"test": True})
        self.assertTrue(result)

    def test_logging_integration(self):
        """Test integration with Django logging."""
        # Test that service works with Django logging
        logger = logging.getLogger(__name__)
        
        # This should not raise any exceptions
        try:
            app_insights.track_event("logging_test", {"logger": "django"})
            logger.info("Application Insights integration test completed")
        except Exception as e:
            self.fail(f"Application Insights integration failed: {e}")

    def test_error_handling(self):
        """Test error handling in Application Insights service."""
        # Test that service handles errors gracefully
        try:
            # Test with invalid parameters
            app_insights.track_event(None, None)
            app_insights.track_metric("", -1)
            app_insights.track_exception(None)
        except Exception as e:
            self.fail(f"Service should handle invalid parameters gracefully: {e}")

    def test_performance_impact(self):
        """Test that Application Insights doesn't significantly impact performance."""
        import time
        
        # Measure time without tracking
        start_time = time.time()
        for _ in range(10):
            pass
        baseline_time = time.time() - start_time
        
        # Ensure baseline time is not zero
        if baseline_time == 0:
            baseline_time = 0.001  # Small non-zero value
        
        # Measure time with tracking
        start_time = time.time()
        for i in range(10):
            app_insights.track_event(f"perf_test_{i}", {"iteration": i})
        tracking_time = time.time() - start_time
        
        # Tracking should not take more than 10x the baseline time
        # (allowing for some overhead but not excessive)
        self.assertLess(tracking_time, baseline_time * 10, 
                       "Application Insights tracking is too slow")


@pytest.mark.integration
class TestApplicationInsightsProduction(TestCase):
    """Production-like tests for Application Insights."""

    def test_production_configuration(self):
        """Test production configuration scenarios."""
        # Test with production-like settings
        with patch.dict('os.environ', {
            'APPLICATIONINSIGHTS_CONNECTION_STRING': 'InstrumentationKey=prod-key;IngestionEndpoint=https://prod.com',
            'ApplicationInsightsAgent_EXTENSION_VERSION': '~3'
        }):
            # Recreate service to pick up new environment variable
            service = ApplicationInsightsService()
            status = service.get_configuration_status()
            
            # In production, we expect these to be configured
            self.assertTrue(status['connection_string_configured'])
            self.assertTrue(status['instrumentation_key_configured'])

    def test_high_volume_tracking(self):
        """Test high volume event tracking."""
        # Test tracking many events quickly
        events = []
        for i in range(100):
            event_name = f"high_volume_event_{i}"
            result = app_insights.track_event(event_name, {"index": i})
            events.append(result)
        
        # All events should be tracked successfully
        self.assertTrue(all(events), "All events should be tracked successfully")

    def test_concurrent_tracking(self):
        """Test concurrent event tracking."""
        import threading
        import time
        
        results = []
        errors = []
        
        def track_event(thread_id):
            try:
                for i in range(10):
                    result = app_insights.track_event(
                        f"concurrent_event_{thread_id}_{i}",
                        {"thread_id": thread_id, "iteration": i}
                    )
                    results.append(result)
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=track_event, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent tracking produced errors: {errors}")
        self.assertEqual(len(results), 50, "All events should be tracked")
        self.assertTrue(all(results), "All events should be tracked successfully")
