"""
Application Insights Service for centralized logging and monitoring.

This service provides a unified interface for logging to Azure Application Insights
with proper error handling and fallback to local logging.
"""

import os
import logging
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class ApplicationInsightsService:
    """
    Service for logging to Azure Application Insights.
    
    Provides methods for tracking events, exceptions, and custom metrics
    with fallback to local logging when Application Insights is not available.
    """
    
    def __init__(self):
        """Initialize the Application Insights service."""
        self.connection_string = self._get_setting('APPLICATIONINSIGHTS_CONNECTION_STRING')
        self.instrumentation_key = self._extract_instrumentation_key()
        self.enabled = bool(self.connection_string)
        
        if self.enabled:
            try:
                from opencensus.ext.azure.log_exporter import AzureLogHandler
                from opencensus.ext.azure.trace_exporter import AzureExporter
                from opencensus.trace.tracer import Tracer
                
                self.log_handler = AzureLogHandler(
                    connection_string=self.connection_string
                )
                self.trace_exporter = AzureExporter(
                    connection_string=self.connection_string
                )
                self.tracer = Tracer(exporter=self.trace_exporter)
                
                logger.info("Application Insights service initialized successfully")
            except ImportError:
                logger.warning("OpenCensus not available, using local logging only")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Application Insights: {e}")
                self.enabled = False
        else:
            logger.info("Application Insights not configured, using local logging only")
    
    def _get_setting(self, setting_name: str) -> Optional[str]:
        """Get setting value with fallback to environment variables."""
        try:
            # Try Django settings first
            return getattr(settings, setting_name, None)
        except Exception:
            # Fallback to environment variables
            return os.environ.get(setting_name)
    
    def _extract_instrumentation_key(self) -> Optional[str]:
        """Extract instrumentation key from connection string."""
        if not self.connection_string:
            return None
        
        try:
            # Parse connection string to extract instrumentation key
            parts = self.connection_string.split(';')
            for part in parts:
                if part.startswith('InstrumentationKey='):
                    return part.split('=')[1]
        except Exception:
            pass
        
        return None
    
    def track_event(
        self, 
        name: str, 
        properties: Optional[Dict[str, Any]] = None,
        measurements: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Track a custom event.
        
        Args:
            name: Event name
            properties: Custom properties
            measurements: Custom measurements
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            if self.enabled and hasattr(self, 'log_handler'):
                # Send to Application Insights
                event_data = {
                    'name': name,
                    'properties': properties or {},
                    'measurements': measurements or {},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.log_handler.emit(logging.LogRecord(
                    name=name,
                    level=logging.INFO,
                    pathname='',
                    lineno=0,
                    msg=json.dumps(event_data),
                    args=(),
                    exc_info=None
                ))
                
                logger.debug(f"Event tracked to Application Insights: {name}")
                return True
            else:
                # Fallback to local logging
                logger.info(f"Event: {name} | Properties: {properties} | Measurements: {measurements}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track event '{name}': {e}")
            return False
    
    def track_exception(
        self, 
        exception: Exception, 
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an exception.
        
        Args:
            exception: The exception to track
            properties: Custom properties
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            if self.enabled and hasattr(self, 'log_handler'):
                # Send to Application Insights
                exception_data = {
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'properties': properties or {},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.log_handler.emit(logging.LogRecord(
                    name='exception',
                    level=logging.ERROR,
                    pathname='',
                    lineno=0,
                    msg=json.dumps(exception_data),
                    args=(),
                    exc_info=(type(exception), exception, exception.__traceback__)
                ))
                
                logger.debug(f"Exception tracked to Application Insights: {type(exception).__name__}")
                return True
            else:
                # Fallback to local logging
                logger.exception(f"Exception: {type(exception).__name__} | Properties: {properties}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track exception: {e}")
            return False
    
    def track_metric(
        self, 
        name: str, 
        value: float, 
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            properties: Custom properties
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            if self.enabled and hasattr(self, 'log_handler'):
                # Send to Application Insights
                metric_data = {
                    'name': name,
                    'value': value,
                    'properties': properties or {},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.log_handler.emit(logging.LogRecord(
                    name=name,
                    level=logging.INFO,
                    pathname='',
                    lineno=0,
                    msg=json.dumps(metric_data),
                    args=(),
                    exc_info=None
                ))
                
                logger.debug(f"Metric tracked to Application Insights: {name} = {value}")
                return True
            else:
                # Fallback to local logging
                logger.info(f"Metric: {name} = {value} | Properties: {properties}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track metric '{name}': {e}")
            return False
    
    def track_dependency(
        self, 
        name: str, 
        dependency_type: str, 
        target: str, 
        duration_ms: float,
        success: bool = True,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a dependency call.
        
        Args:
            name: Dependency name
            dependency_type: Type of dependency (HTTP, SQL, etc.)
            target: Target of the dependency
            duration_ms: Duration in milliseconds
            success: Whether the call was successful
            properties: Custom properties
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            if self.enabled and hasattr(self, 'tracer'):
                # Send to Application Insights using tracer
                with self.tracer.span(name=name) as span:
                    span.add_attribute('dependency.type', dependency_type)
                    span.add_attribute('dependency.target', target)
                    span.add_attribute('dependency.duration_ms', duration_ms)
                    span.add_attribute('dependency.success', success)
                    
                    if properties:
                        for key, value in properties.items():
                            span.add_attribute(f'dependency.{key}', str(value))
                
                logger.debug(f"Dependency tracked to Application Insights: {name}")
                return True
            else:
                # Fallback to local logging
                status = "SUCCESS" if success else "FAILED"
                logger.info(f"Dependency: {name} ({dependency_type}) -> {target} | Duration: {duration_ms}ms | Status: {status} | Properties: {properties}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track dependency '{name}': {e}")
            return False
    
    def track_request(
        self, 
        name: str, 
        url: str, 
        method: str, 
        duration_ms: float,
        status_code: int,
        success: bool = True,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an HTTP request.
        
        Args:
            name: Request name
            url: Request URL
            method: HTTP method
            duration_ms: Duration in milliseconds
            status_code: HTTP status code
            success: Whether the request was successful
            properties: Custom properties
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            if self.enabled and hasattr(self, 'tracer'):
                # Send to Application Insights using tracer
                with self.tracer.span(name=name) as span:
                    span.add_attribute('http.url', url)
                    span.add_attribute('http.method', method)
                    span.add_attribute('http.duration_ms', duration_ms)
                    span.add_attribute('http.status_code', status_code)
                    span.add_attribute('http.success', success)
                    
                    if properties:
                        for key, value in properties.items():
                            span.add_attribute(f'request.{key}', str(value))
                
                logger.debug(f"Request tracked to Application Insights: {name}")
                return True
            else:
                # Fallback to local logging
                status = "SUCCESS" if success else "FAILED"
                logger.info(f"Request: {name} | {method} {url} | Duration: {duration_ms}ms | Status: {status_code} ({status}) | Properties: {properties}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track request '{name}': {e}")
            return False
    
    def track_whatsapp_message(
        self,
        phone_number: str,
        message_type: str,
        success: bool,
        duration_ms: float = 0,
        error_message: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track WhatsApp message events.
        
        Args:
            phone_number: Recipient phone number
            message_type: Type of message (text, template, etc.)
            success: Whether the message was sent successfully
            duration_ms: Processing duration in milliseconds
            error_message: Error message if failed
            properties: Custom properties
            
        Returns:
            True if tracked successfully, False otherwise
        """
        try:
            # Prepare properties
            event_properties = {
                'phone_number': phone_number,
                'message_type': message_type,
                'success': success,
                'duration_ms': duration_ms
            }
            
            if error_message:
                event_properties['error_message'] = error_message
            
            if properties:
                event_properties.update(properties)
            
            # Track as event
            event_name = f"WhatsAppMessage_{message_type.capitalize()}"
            return self.track_event(event_name, event_properties)
            
        except Exception as e:
            logger.error(f"Failed to track WhatsApp message: {e}")
            return False
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the configuration status of the service."""
        return {
            'enabled': self.enabled,
            'connection_string_configured': bool(self.connection_string),
            'instrumentation_key_configured': bool(self.instrumentation_key),
            'opencensus_available': self.enabled and hasattr(self, 'log_handler')
        }


# Global instance for easy access
app_insights = ApplicationInsightsService()
