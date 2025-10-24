#!/usr/bin/env python3
"""
Test script to check API URL imports
"""

import os
import sys
import django  # pyright: reportMissingImports=false

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_api_imports():
    """Test if API URLs can be imported correctly."""
    print("Testing API URL imports...")
    
    try:
        from apps.embeddings.api_urls_simple import urlpatterns
        print(f"✅ API URLs imported successfully")
        print(f"Number of URL patterns: {len(urlpatterns)}")
        
        for i, pattern in enumerate(urlpatterns):
            print(f"  {i+1}. {pattern.pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing API URLs: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_urls():
    """Test if main URLs include API URLs."""
    print("\nTesting main URL configuration...")
    
    try:
        from config.urls import urlpatterns
        print(f"✅ Main URLs imported successfully")
        print(f"Number of main URL patterns: {len(urlpatterns)}")
        
        api_found = False
        for pattern in urlpatterns:
            if 'api/v1/' in str(pattern.pattern):
                api_found = True
                print(f"  Found API pattern: {pattern.pattern}")
        
        if not api_found:
            print("❌ API URLs not found in main URL patterns")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing main URLs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Django API URL Configuration")
    print("=" * 50)
    
    success = True
    success &= test_api_imports()
    success &= test_main_urls()
    
    if success:
        print("\n🎉 All tests passed! API URLs are configured correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1) 