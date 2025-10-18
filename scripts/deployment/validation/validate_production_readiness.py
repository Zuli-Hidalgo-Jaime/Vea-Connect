#!/usr/bin/env python3
"""
WhatsApp Bot Production Readiness Validation Script.

This script validates all components of the WhatsApp Bot implementation
to ensure it's ready for production deployment.
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionValidator:
    """Validates WhatsApp Bot production readiness."""
    
    def __init__(self):
        """Initialize validator."""
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PENDING',
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warnings': 0
            }
        }
    
    def add_check_result(self, check_name: str, status: str, details: str = '', warning: bool = False):
        """Add a check result to the validation results."""
        self.results['checks'][check_name] = {
            'status': status,
            'details': details,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total_checks'] += 1
        
        if status == 'PASS':
            self.results['summary']['passed_checks'] += 1
        elif status == 'FAIL':
            self.results['summary']['failed_checks'] += 1
        elif status == 'WARNING':
            self.results['summary']['warnings'] += 1
    
    def check_environment_variables(self) -> bool:
        """Check if all required environment variables are set."""
        logger.info("🔍 Checking environment variables...")
        
        required_vars = [
            'ACS_WHATSAPP_ENDPOINT',
            'ACS_WHATSAPP_API_KEY', 
            'ACS_PHONE_NUMBER',
            'WHATSAPP_CHANNEL_ID_GUID',
            'DATABASE_URL',
            'OPENAI_API_KEY'
        ]
        
        optional_vars = [
            'EVENT_GRID_VALIDATION_KEY'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            self.add_check_result(
                'environment_variables',
                'FAIL',
                f"Missing required variables: {', '.join(missing_required)}"
            )
            return False
        
        if missing_optional:
            self.add_check_result(
                'environment_variables',
                'WARNING',
                f"Missing optional variables: {', '.join(missing_optional)}"
            )
        else:
            self.add_check_result(
                'environment_variables',
                'PASS',
                "All environment variables configured"
            )
        
        return len(missing_required) == 0
    
    def check_database_connection(self) -> bool:
        """Check database connectivity and migrations."""
        logger.info("🔍 Checking database connection...")
        
        try:
            import django
            from django.conf import settings
            from django.db import connection
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check if migrations are applied
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('showmigrations', 'whatsapp_bot', stdout=out)
            migrations_output = out.getvalue()
            
            if '[X]' in migrations_output:
                self.add_check_result(
                    'database_connection',
                    'PASS',
                    "Database connected and migrations applied"
                )
                return True
            else:
                self.add_check_result(
                    'database_connection',
                    'FAIL',
                    "Database connected but migrations not applied"
                )
                return False
                
        except Exception as e:
            self.add_check_result(
                'database_connection',
                'FAIL',
                f"Database connection failed: {str(e)}"
            )
            return False
    

    
    def check_acs_configuration(self) -> bool:
        """Check ACS configuration and connectivity."""
        logger.info("🔍 Checking ACS configuration...")
        
        try:
            from apps.whatsapp_bot.services import ACSService
            
            acs_service = ACSService()
            
            # Check if configuration is valid
            if not acs_service.endpoint or not acs_service.access_key:
                self.add_check_result(
                    'acs_configuration',
                    'FAIL',
                    "ACS endpoint or access key not configured"
                )
                return False
            
            # Test ACS connectivity (without sending actual message)
            test_url = f"{acs_service.endpoint}/messages"
            headers = {
                'Authorization': f'HMAC-SHA256 {acs_service.access_key}',
                'Content-Type': 'application/json'
            }
            
            # This will fail with 400/401 but confirms connectivity
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code in [400, 401, 403]:
                self.add_check_result(
                    'acs_configuration',
                    'PASS',
                    f"ACS endpoint accessible (status: {response.status_code})"
                )
                return True
            else:
                self.add_check_result(
                    'acs_configuration',
                    'WARNING',
                    f"ACS endpoint responded with unexpected status: {response.status_code}"
                )
                return True
                
        except Exception as e:
            self.add_check_result(
                'acs_configuration',
                'FAIL',
                f"ACS configuration check failed: {str(e)}"
            )
            return False
    
    def check_whatsapp_templates(self) -> bool:
        """Check if WhatsApp templates are configured."""
        logger.info("🔍 Checking WhatsApp templates...")
        
        try:
            from apps.whatsapp_bot.models import WhatsAppTemplate
            
            templates = WhatsAppTemplate.objects.all()
            
            required_templates = [
                'vea_info_donativos',
                'vea_contacto_ministerio', 
                'vea_event_info',
                'vea_request_received'
            ]
            
            configured_templates = [t.name for t in templates]
            missing_templates = [t for t in required_templates if t not in configured_templates]
            
            if missing_templates:
                self.add_check_result(
                    'whatsapp_templates',
                    'FAIL',
                    f"Missing templates: {', '.join(missing_templates)}"
                )
                return False
            else:
                self.add_check_result(
                    'whatsapp_templates',
                    'PASS',
                    f"All {len(configured_templates)} templates configured"
                )
                return True
                
        except Exception as e:
            self.add_check_result(
                'whatsapp_templates',
                'FAIL',
                f"Template check failed: {str(e)}"
            )
            return False
    
    def check_openai_configuration(self) -> bool:
        """Check OpenAI configuration."""
        logger.info("🔍 Checking OpenAI configuration...")
        
        try:
            from apps.embeddings.openai_service import OpenAIService
            
            openai_service = OpenAIService()
            
            # Test OpenAI connectivity
            response = openai_service.client.models.list()
            
            self.add_check_result(
                'openai_configuration',
                'PASS',
                "OpenAI API accessible"
            )
            return True
            
        except Exception as e:
            self.add_check_result(
                'openai_configuration',
                'WARNING',
                f"OpenAI configuration issue: {str(e)}"
            )
            return True  # Warning, not fail, as it's fallback
    
    def check_event_grid_handler(self) -> bool:
        """Check Event Grid handler implementation."""
        logger.info("🔍 Checking Event Grid handler...")
        
        try:
            from apps.whatsapp_bot.event_grid_handler import (
                EventGridHandler,
                EventGridValidator,
                WhatsAppEventProcessor
            )
            
            # Test handler initialization
            validator = EventGridValidator()
            processor = WhatsAppEventProcessor(
                user_service=None,
                template_service=None,
                logging_service=None,
                storage_service=None
            )
            
            self.add_check_result(
                'event_grid_handler',
                'PASS',
                "Event Grid handler classes importable and initializable"
            )
            return True
            
        except Exception as e:
            self.add_check_result(
                'event_grid_handler',
                'FAIL',
                f"Event Grid handler check failed: {str(e)}"
            )
            return False
    
    def check_azure_function_ready(self) -> bool:
        """Check if code is ready for Azure Functions deployment."""
        logger.info("🔍 Checking Azure Function readiness...")
        
        try:
            # Check if Azure Function example exists
            function_file = 'apps/whatsapp_bot/azure_function_example.py'
            if not os.path.exists(function_file):
                self.add_check_result(
                    'azure_function_ready',
                    'FAIL',
                    "Azure Function example file not found"
                )
                return False
            
            # Check if function.json exists
            function_json = 'apps/whatsapp_bot/function.json'
            if not os.path.exists(function_json):
                self.add_check_result(
                    'azure_function_ready',
                    'WARNING',
                    "function.json not found (will be created during deployment)"
                )
            
            self.add_check_result(
                'azure_function_ready',
                'PASS',
                "Code structure ready for Azure Functions deployment"
            )
            return True
            
        except Exception as e:
            self.add_check_result(
                'azure_function_ready',
                'FAIL',
                f"Azure Function readiness check failed: {str(e)}"
            )
            return False
    
    def check_unit_tests(self) -> bool:
        """Check if unit tests are available and can be run."""
        logger.info("🔍 Checking unit tests...")
        
        try:
            # Check if test files exist
            test_files = [
                'apps/whatsapp_bot/tests.py',
                'apps/whatsapp_bot/tests_event_grid.py'
            ]
            
            missing_tests = [f for f in test_files if not os.path.exists(f)]
            
            if missing_tests:
                self.add_check_result(
                    'unit_tests',
                    'FAIL',
                    f"Missing test files: {', '.join(missing_tests)}"
                )
                return False
            
            # Try to import test modules
            import apps.whatsapp_bot.tests
            import apps.whatsapp_bot.tests_event_grid
            
            self.add_check_result(
                'unit_tests',
                'PASS',
                f"All {len(test_files)} test files available and importable"
            )
            return True
            
        except Exception as e:
            self.add_check_result(
                'unit_tests',
                'WARNING',
                f"Unit test check issue: {str(e)}"
            )
            return True
    
    def check_logging_configuration(self) -> bool:
        """Check logging configuration."""
        logger.info("🔍 Checking logging configuration...")
        
        try:
            # Test logging
            test_logger = logging.getLogger('whatsapp_bot_test')
            test_logger.info("Test log message")
            
            self.add_check_result(
                'logging_configuration',
                'PASS',
                "Logging system functional"
            )
            return True
            
        except Exception as e:
            self.add_check_result(
                'logging_configuration',
                'FAIL',
                f"Logging configuration failed: {str(e)}"
            )
            return False
    
    def check_security_configuration(self) -> bool:
        """Check security-related configurations."""
        logger.info("🔍 Checking security configuration...")
        
        try:
            # Check if DEBUG is disabled in production
            debug_enabled = os.getenv('DEBUG', 'False').lower() == 'true'
            
            if debug_enabled:
                self.add_check_result(
                    'security_configuration',
                    'WARNING',
                    "DEBUG mode is enabled (should be disabled in production)"
                )
            else:
                self.add_check_result(
                    'security_configuration',
                    'PASS',
                    "DEBUG mode is disabled"
                )
            
            # Check if secret key is configured
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key or secret_key == 'dev-secret-key-unsafe':
                self.add_check_result(
                    'security_configuration',
                    'FAIL',
                    "SECRET_KEY not properly configured"
                )
                return False
            
            return True
            
        except Exception as e:
            self.add_check_result(
                'security_configuration',
                'FAIL',
                f"Security configuration check failed: {str(e)}"
            )
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all production readiness checks."""
        logger.info("🚀 Starting WhatsApp Bot Production Readiness Validation")
        logger.info("=" * 60)
        
        checks = [
            ('Environment Variables', self.check_environment_variables),
            ('Database Connection', self.check_database_connection),

            ('ACS Configuration', self.check_acs_configuration),
            ('WhatsApp Templates', self.check_whatsapp_templates),
            ('OpenAI Configuration', self.check_openai_configuration),
            ('Event Grid Handler', self.check_event_grid_handler),
            ('Azure Function Ready', self.check_azure_function_ready),
            ('Unit Tests', self.check_unit_tests),
            ('Logging Configuration', self.check_logging_configuration),
            ('Security Configuration', self.check_security_configuration),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.add_check_result(
                    check_name.lower().replace(' ', '_'),
                    'FAIL',
                    f"Check failed with exception: {str(e)}"
                )
        
        # Determine overall status
        failed_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'FAIL')
        
        if failed_checks == 0:
            self.results['overall_status'] = 'READY'
        elif failed_checks <= 2:
            self.results['overall_status'] = 'WARNING'
        else:
            self.results['overall_status'] = 'NOT_READY'
        
        return self.results
    
    def print_results(self):
        """Print validation results in a formatted way."""
        print("\n" + "=" * 60)
        print("📊 WHATSAPP BOT PRODUCTION READINESS REPORT")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['overall_status']}")
        print()
        
        # Print check results
        for check_name, check_result in self.results['checks'].items():
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'WARNING': '⚠️'
            }.get(check_result['status'], '❓')
            
            print(f"{status_icon} {check_name.replace('_', ' ').title()}")
            print(f"   Status: {check_result['status']}")
            if check_result['details']:
                print(f"   Details: {check_result['details']}")
            print()
        
        # Print summary
        summary = self.results['summary']
        print("-" * 60)
        print("📈 SUMMARY")
        print("-" * 60)
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed_checks']} ✅")
        print(f"Failed: {summary['failed_checks']} ❌")
        print(f"Warnings: {summary['warnings']} ⚠️")
        print()
        
        # Print recommendations
        print("🎯 RECOMMENDATIONS")
        print("-" * 60)
        
        if self.results['overall_status'] == 'READY':
            print("✅ WhatsApp Bot is ready for production deployment!")
            print("   • All critical checks passed")
            print("   • Review warnings if any")
            print("   • Proceed with deployment")
        elif self.results['overall_status'] == 'WARNING':
            print("⚠️  WhatsApp Bot has some issues that should be addressed:")
            failed_checks = [name for name, result in self.results['checks'].items() if result['status'] == 'FAIL']
            for check in failed_checks:
                print(f"   • Fix: {check.replace('_', ' ').title()}")
            print("   • Review and address issues before deployment")
        else:
            print("❌ WhatsApp Bot is not ready for production:")
            failed_checks = [name for name, result in self.results['checks'].items() if result['status'] == 'FAIL']
            for check in failed_checks:
                print(f"   • Critical: {check.replace('_', ' ').title()}")
            print("   • Address all critical issues before deployment")
        
        print("\n" + "=" * 60)


def main():
    """Main validation function."""
    try:
        # Set up Django environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        
        import django
        django.setup()
        
        # Run validation
        validator = ProductionValidator()
        results = validator.run_all_checks()
        validator.print_results()
        
        # Save results to file
        with open('production_validation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: production_validation_results.json")
        
        # Exit with appropriate code
        if results['overall_status'] == 'READY':
            sys.exit(0)
        elif results['overall_status'] == 'WARNING':
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        sys.exit(3)


if __name__ == '__main__':
    main() 