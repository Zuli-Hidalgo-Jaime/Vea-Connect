#!/usr/bin/env python3
"""
Unified Diagnostics Script for VEA Connect WebApp
Consolidates all diagnostic functionality into a single, modular script
"""
import os
import sys
import django
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import json

# Configure Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Cargar variables de entorno desde functions/local.settings.json
def load_env_from_functions():
    """Carga variables de entorno desde functions/local.settings.json"""
    functions_settings_path = BASE_DIR / "functions" / "local.settings.json"
    
    if functions_settings_path.exists():
        try:
            with open(functions_settings_path, 'r') as f:
                settings = json.load(f)
            
            values = settings.get('Values', {})
            
            # Variables críticas que necesitamos
            critical_vars = [
                'AZURE_STORAGE_CONNECTION_STRING',
                'AZURE_STORAGE_ACCOUNT_NAME', 
                'AZURE_STORAGE_ACCOUNT_KEY',
                'AZURE_STORAGE_CONTAINER_NAME',
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_API_KEY',
                'AZURE_OPENAI_CHAT_DEPLOYMENT',
                'AZURE_OPENAI_CHAT_API_VERSION',
                'AZURE_SEARCH_ENDPOINT',
                'AZURE_SEARCH_KEY',
                'AZURE_SEARCH_INDEX_NAME',
                'ACS_WHATSAPP_ENDPOINT',
                'ACS_WHATSAPP_API_KEY',
                'ACS_PHONE_NUMBER',
                'WHATSAPP_CHANNEL_ID_GUID',
                'AZURE_REDIS_CONNECTIONSTRING',
                'VISION_ENDPOINT',
                'VISION_KEY',
                'SECRET_KEY',
                'FUNCTION_APP_URL'
            ]
            
            loaded_count = 0
            for var in critical_vars:
                value = values.get(var)
                if value:
                    os.environ[var] = value
                    loaded_count += 1
            
            print(f"✅ Variables de entorno cargadas: {loaded_count}/{len(critical_vars)}")
        except Exception as e:
            print(f"⚠️ No se pudieron cargar variables desde functions/local.settings.json: {e}")

# Cargar variables antes de configurar Django
load_env_from_functions()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document
from services.storage_service import azure_storage
from services.search_index_service import SearchIndexService
from services.redis_cache import WhatsAppCacheService
from services.whatsapp_sender import WhatsAppSenderService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()

class DiagnosticRunner:
    """Main diagnostic runner class"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def run_all_diagnostics(self) -> Dict[str, Any]:
        """Run all diagnostic tests"""
        logger.info("Starting comprehensive system diagnostics")
        
        diagnostics = [
            ("storage_service", self.test_storage_service),
            ("database_connection", self.test_database_connection),
            ("documents_in_db", self.test_documents_in_db),
            ("ai_search_service", self.test_ai_search_service),
            ("redis_cache", self.test_redis_cache),
            ("whatsapp_sender", self.test_whatsapp_sender),
            ("openai_integration", self.test_openai_integration),
            ("azure_functions", self.test_azure_functions),
            ("environment_variables", self.test_environment_variables),
        ]
        
        for name, diagnostic_func in diagnostics:
            try:
                logger.info(f"Running {name} diagnostic")
                result = diagnostic_func()
                self.results[name] = result
            except Exception as e:
                logger.error(f"Error in {name} diagnostic: {e}")
                self.errors.append(f"{name}: {str(e)}")
                self.results[name] = {"status": "error", "message": str(e)}
        
        return self.generate_report()
    
    def test_storage_service(self) -> Dict[str, Any]:
        """Test Azure Storage service"""
        try:
            status = azure_storage.get_configuration_status()
            
            if not status.get('client_initialized', False):
                return {"status": "failed", "message": "Storage client not initialized"}
            
            # Test basic operations
            list_result = azure_storage.list_blobs(max_results=5)
            if not list_result.get('success'):
                return {"status": "failed", "message": f"List blobs failed: {list_result.get('error')}"}
            
            return {
                "status": "success",
                "blobs_count": len(list_result.get('blobs', [])),
                "configuration": status
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {"status": "success", "message": "Database connection successful"}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    def test_documents_in_db(self) -> Dict[str, Any]:
        """Test documents in database"""
        try:
            documents = Document.objects.all()
            count = documents.count()
            
            return {
                "status": "success",
                "documents_count": count,
                "sample_documents": [
                    {"id": doc.id, "title": doc.title, "file_type": doc.file_type}
                    for doc in documents[:3]
                ]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_ai_search_service(self) -> Dict[str, Any]:
        """Test Azure AI Search service"""
        try:
            search_service = SearchIndexService()
            
            if not search_service.client:
                return {"status": "failed", "message": "AI Search client not initialized"}
            
            # Test simple search
            results = search_service.search("test", top=3)
            
            return {
                "status": "success",
                "results_count": len(results) if results else 0,
                "client_initialized": True
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_redis_cache(self) -> Dict[str, Any]:
        """Test Redis cache service"""
        try:
            cache_service = WhatsAppCacheService()
            
            # Test basic operations
            test_key = "test_diagnostic"
            test_data = {"test": "data", "timestamp": "2024-01-01"}
            
            store_result = cache_service.store_conversation_context(test_key, test_data)
            retrieved_data = cache_service.get_conversation_context(test_key)
            
            return {
                "status": "success" if store_result else "partial",
                "store_working": store_result,
                "retrieve_working": retrieved_data is not None
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_whatsapp_sender(self) -> Dict[str, Any]:
        """Test WhatsApp sender service"""
        try:
            sender_service = WhatsAppSenderService()
            config_status = sender_service.validate_configuration()
            
            return {
                "status": "success" if config_status.get('all_configured') else "partial",
                "configuration": config_status
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_openai_integration(self) -> Dict[str, Any]:
        """Test Azure OpenAI integration"""
        try:
            from openai import AzureOpenAI
            
            required_vars = [
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_API_KEY',
                'AZURE_OPENAI_CHAT_DEPLOYMENT'
            ]
            
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                return {"status": "failed", "message": f"Missing environment variables: {missing_vars}"}
            
            # Test client initialization
            client = AzureOpenAI(
                azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
                api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
                api_version=os.environ.get('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview')
            )
            
            return {"status": "success", "client_initialized": True}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_azure_functions(self) -> Dict[str, Any]:
        """Test Azure Functions connectivity"""
        try:
            import requests
            
            function_url = os.environ.get('FUNCTION_APP_URL')
            if not function_url:
                return {"status": "skipped", "message": "FUNCTION_APP_URL not configured"}
            
            # Test health endpoint
            health_url = f"{function_url}/health"
            response = requests.get(health_url, timeout=10)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test critical environment variables"""
        critical_vars = [
            'SECRET_KEY',
            'AZURE_STORAGE_ACCOUNT_NAME',
            'AZURE_STORAGE_ACCOUNT_KEY',
            'AZURE_POSTGRESQL_HOST',
            'AZURE_POSTGRESQL_NAME',
            'AZURE_POSTGRESQL_USERNAME',
            'AZURE_POSTGRESQL_PASSWORD',
        ]
        
        missing_vars = []
        configured_vars = []
        
        for var in critical_vars:
            if os.environ.get(var):
                configured_vars.append(var)
            else:
                missing_vars.append(var)
        
        return {
            "status": "success" if not missing_vars else "partial",
            "configured_vars": len(configured_vars),
            "missing_vars": missing_vars,
            "total_critical_vars": len(critical_vars)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        successful_tests = sum(1 for result in self.results.values() if result.get('status') == 'success')
        total_tests = len(self.results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": self.results,
            "errors": self.errors,
            "timestamp": str(django.utils.timezone.now())
        }

def main():
    """Main function"""
    runner = DiagnosticRunner()
    report = runner.run_all_diagnostics()
    
    # Print summary
    summary = report['summary']
    print(f"\nDiagnostic Summary:")
    print(f"Total tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    
    # Print detailed results
    print(f"\nDetailed Results:")
    for test_name, result in report['results'].items():
        status = result.get('status', 'unknown')
        status_icon = "✓" if status == 'success' else "✗" if status == 'failed' else "⚠"
        print(f"{status_icon} {test_name}: {status}")
        if result.get('message'):
            print(f"  Message: {result['message']}")
    
    # Print errors if any
    if report['errors']:
        print(f"\nErrors:")
        for error in report['errors']:
            print(f"  - {error}")
    
    # Save report to file
    report_file = BASE_DIR / "logs" / "diagnostic_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return 0 if summary['success_rate'] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
