"""
Storage Service for WhatsApp Bot.

This module provides storage functionality for delivery reports,
file storage, and data persistence operations.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.db import connection, transaction
from django.core.cache import cache
from .event_grid_handler import DeliveryReport

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for handling storage operations.
    
    This service manages delivery reports, file storage, and
    data persistence with proper error handling and caching.
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize Storage Service.
        
        Args:
            cache_ttl: Cache TTL in seconds for cached data
        """
        self.cache_ttl = cache_ttl
    
    def save_delivery_report(self, report: DeliveryReport) -> bool:
        """
        Save delivery report to storage.
        
        Args:
            report: Delivery report data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_delivery_reports (
                            message_id, status, timestamp, recipient_number,
                            channel_registration_id, error_details, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, NOW()
                        )
                        ON CONFLICT (message_id) 
                        DO UPDATE SET
                            status = EXCLUDED.status,
                            timestamp = EXCLUDED.timestamp,
                            error_details = EXCLUDED.error_details,
                            updated_at = NOW()
                    """, [
                        report.message_id,
                        report.status,
                        report.timestamp,
                        report.recipient_number,
                        report.channel_registration_id,
                        json.dumps(report.error_details) if report.error_details else None
                    ])
                    
                    logger.info(f"Saved delivery report for message {report.message_id}: {report.status}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving delivery report for {report.message_id}: {e}")
            return False
    
    def get_delivery_report(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get delivery report by message ID.
        
        Args:
            message_id: Message ID to retrieve
            
        Returns:
            Delivery report dictionary or None if not found
        """
        try:
            # Try cache first
            cache_key = f"delivery_report:{message_id}"
            cached_report = cache.get(cache_key)
            
            if cached_report:
                logger.info(f"Retrieved delivery report from cache: {message_id}")
                return cached_report
            
            # Query database
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        message_id, status, timestamp, recipient_number,
                        channel_registration_id, error_details, created_at, updated_at
                    FROM whatsapp_delivery_reports 
                    WHERE message_id = %s
                """, [message_id])
                
                row = cursor.fetchone()
                
                if row:
                    report_data = {
                        'message_id': row[0],
                        'status': row[1],
                        'timestamp': row[2].isoformat() if row[2] else None,
                        'recipient_number': row[3],
                        'channel_registration_id': row[4],
                        'error_details': json.loads(row[5]) if row[5] else None,
                        'created_at': row[6].isoformat() if row[6] else None,
                        'updated_at': row[7].isoformat() if row[7] else None
                    }
                    
                    # Cache report data
                    cache.set(cache_key, report_data, self.cache_ttl)
                    
                    logger.info(f"Retrieved delivery report from database: {message_id}")
                    return report_data
                else:
                    logger.info(f"Delivery report not found: {message_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting delivery report {message_id}: {e}")
            return None
    
    def get_delivery_reports_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get delivery reports by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of reports to return
            
        Returns:
            List of delivery report dictionaries
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        message_id, status, timestamp, recipient_number,
                        channel_registration_id, error_details, created_at
                    FROM whatsapp_delivery_reports 
                    WHERE status = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, [status, limit])
                
                rows = cursor.fetchall()
                
                reports = []
                for row in rows:
                    reports.append({
                        'message_id': row[0],
                        'status': row[1],
                        'timestamp': row[2].isoformat() if row[2] else None,
                        'recipient_number': row[3],
                        'channel_registration_id': row[4],
                        'error_details': json.loads(row[5]) if row[5] else None,
                        'created_at': row[6].isoformat() if row[6] else None
                    })
                
                logger.info(f"Retrieved {len(reports)} delivery reports with status: {status}")
                return reports
                
        except Exception as e:
            logger.error(f"Error getting delivery reports by status {status}: {e}")
            return []
    
    def get_delivery_statistics(self) -> Dict[str, Any]:
        """
        Get delivery statistics.
        
        Returns:
            Delivery statistics dictionary
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_reports,
                        COUNT(CASE WHEN status = 'Delivered' THEN 1 END) as delivered,
                        COUNT(CASE WHEN status = 'Failed' THEN 1 END) as failed,
                        COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN error_details IS NOT NULL THEN 1 END) as with_errors
                    FROM whatsapp_delivery_reports
                """)
                
                row = cursor.fetchone()
                
                if row:
                    stats = {
                        'total_reports': row[0],
                        'delivered': row[1],
                        'failed': row[2],
                        'pending': row[3],
                        'with_errors': row[4]
                    }
                    
                    # Calculate delivery rate
                    if stats['total_reports'] > 0:
                        stats['delivery_rate'] = (stats['delivered'] / stats['total_reports']) * 100
                        stats['failure_rate'] = (stats['failed'] / stats['total_reports']) * 100
                    else:
                        stats['delivery_rate'] = 0
                        stats['failure_rate'] = 0
                    
                    logger.info(f"Retrieved delivery statistics: {stats['delivery_rate']:.1f}% delivery rate")
                    return stats
                else:
                    return {
                        'total_reports': 0,
                        'delivered': 0,
                        'failed': 0,
                        'pending': 0,
                        'with_errors': 0,
                        'delivery_rate': 0,
                        'failure_rate': 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting delivery statistics: {e}")
            return {
                'total_reports': 0,
                'delivered': 0,
                'failed': 0,
                'pending': 0,
                'with_errors': 0,
                'delivery_rate': 0,
                'failure_rate': 0,
                'error': str(e)
            }
    
    def save_interaction_log(self, interaction_data: Dict[str, Any]) -> bool:
        """
        Save interaction log to storage.
        
        Args:
            interaction_data: Interaction data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_interaction_logs (
                            phone_number, message_text, intent_detected,
                            template_used, response_text, response_id,
                            parameters_used, fallback_used, processing_time_ms,
                            success, error_message, context_data, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                    """, [
                        interaction_data.get('phone_number'),
                        interaction_data.get('message_text'),
                        interaction_data.get('intent_detected'),
                        interaction_data.get('template_used'),
                        interaction_data.get('response_text'),
                        interaction_data.get('response_id'),
                        json.dumps(interaction_data.get('parameters_used', {})),
                        interaction_data.get('fallback_used', False),
                        interaction_data.get('processing_time_ms', 0),
                        interaction_data.get('success', False),
                        interaction_data.get('error_message'),
                        json.dumps(interaction_data.get('context_data', {}))
                    ])
                    
                    logger.info(f"Saved interaction log for {interaction_data.get('phone_number')}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving interaction log: {e}")
            return False
    
    def save_event_grid_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Save Event Grid event for audit purposes.
        
        Args:
            event_data: Event Grid event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_event_grid_logs (
                            event_id, event_type, event_time, data, created_at
                        ) VALUES (
                            %s, %s, %s, %s, NOW()
                        )
                    """, [
                        event_data.get('id'),
                        event_data.get('eventType'),
                        event_data.get('eventTime'),
                        json.dumps(event_data)
                    ])
                    
                    logger.info(f"Saved Event Grid event: {event_data.get('eventType')}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving Event Grid event: {e}")
            return False
    
    def get_storage_health_status(self) -> Dict[str, Any]:
        """
        Get storage health status.
        
        Returns:
            Storage health status dictionary
        """
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_healthy = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False
        
        # Test cache connection
        try:
            cache.set('health_check', 'ok', 60)
            cache_healthy = cache.get('health_check') == 'ok'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            cache_healthy = False
        
        # Get storage statistics
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM whatsapp_delivery_reports")
                delivery_reports_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM whatsapp_interaction_logs")
                interaction_logs_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM whatsapp_event_grid_logs")
                event_grid_logs_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            delivery_reports_count = 0
            interaction_logs_count = 0
            event_grid_logs_count = 0
        
        return {
            'database_healthy': db_healthy,
            'cache_healthy': cache_healthy,
            'delivery_reports_count': delivery_reports_count,
            'interaction_logs_count': interaction_logs_count,
            'event_grid_logs_count': event_grid_logs_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data from storage.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cleanup_results = {}
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Clean up old delivery reports
                    cursor.execute("""
                        DELETE FROM whatsapp_delivery_reports 
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, [days_to_keep])
                    cleanup_results['delivery_reports_deleted'] = cursor.rowcount
                    
                    # Clean up old interaction logs
                    cursor.execute("""
                        DELETE FROM whatsapp_interaction_logs 
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, [days_to_keep])
                    cleanup_results['interaction_logs_deleted'] = cursor.rowcount
                    
                    # Clean up old Event Grid logs
                    cursor.execute("""
                        DELETE FROM whatsapp_event_grid_logs 
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, [days_to_keep])
                    cleanup_results['event_grid_logs_deleted'] = cursor.rowcount
            
            total_deleted = sum(cleanup_results.values())
            logger.info(f"Cleanup completed: {total_deleted} records deleted")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {
                'delivery_reports_deleted': 0,
                'interaction_logs_deleted': 0,
                'event_grid_logs_deleted': 0,
                'error': str(e)
            }
    
    def export_data_for_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """
        Export data for analysis.
        
        Args:
            start_date: Start date for export
            end_date: End date for export
            
        Returns:
            Dictionary containing exported data
        """
        try:
            export_data = {}
            
            # Export delivery reports
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        message_id, status, timestamp, recipient_number,
                        error_details, created_at
                    FROM whatsapp_delivery_reports 
                    WHERE created_at BETWEEN %s AND %s
                    ORDER BY created_at
                """, [start_date, end_date])
                
                rows = cursor.fetchall()
                export_data['delivery_reports'] = []
                
                for row in rows:
                    export_data['delivery_reports'].append({
                        'message_id': row[0],
                        'status': row[1],
                        'timestamp': row[2].isoformat() if row[2] else None,
                        'recipient_number': row[3],
                        'error_details': json.loads(row[4]) if row[4] else None,
                        'created_at': row[5].isoformat() if row[5] else None
                    })
            
            # Export interaction logs
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        phone_number, message_text, intent_detected,
                        template_used, fallback_used, processing_time_ms,
                        success, created_at
                    FROM whatsapp_interaction_logs 
                    WHERE created_at BETWEEN %s AND %s
                    ORDER BY created_at
                """, [start_date, end_date])
                
                rows = cursor.fetchall()
                export_data['interaction_logs'] = []
                
                for row in rows:
                    export_data['interaction_logs'].append({
                        'phone_number': row[0],
                        'message_text': row[1],
                        'intent_detected': row[2],
                        'template_used': row[3],
                        'fallback_used': row[4],
                        'processing_time_ms': row[5],
                        'success': row[6],
                        'created_at': row[7].isoformat() if row[7] else None
                    })
            
            logger.info(f"Exported {len(export_data['delivery_reports'])} delivery reports and {len(export_data['interaction_logs'])} interaction logs")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {
                'delivery_reports': [],
                'interaction_logs': [],
                'error': str(e)
            } 