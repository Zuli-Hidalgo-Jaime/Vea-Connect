#!/usr/bin/env python3
"""
Test script to check API URLs with proper Django configuration
"""

import os
import sys
import django  # pyright: reportMissingImports=false

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_api_imports():
    """Test if API components can be imported correctly."""
    print("🔍 Testing API imports...")
    
    try:
        # Test API views
        from apps.embeddings.api_views import (
            EmbeddingViewSet, SearchViewSet, HealthCheckView, 
            StatisticsView, SearchLogViewSet
        )
        print("✅ API views imported successfully")
        
        # Test serializers
        from apps.embeddings.serializers import (
            EmbeddingSerializer, SearchQuerySerializer, HealthCheckSerializer
        )
        print("✅ API serializers imported successfully")
        
        # Test models
        from apps.embeddings.models import Embedding, EmbeddingSearchLog
        print("✅ API models imported successfully")
        
        # Test JWT views
        from rest_framework_simplejwt.views import (
            TokenObtainPairView, TokenRefreshView, TokenVerifyView
        )
        print("✅ JWT views imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing API components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_urls():
    """Test if API URLs can be loaded correctly."""
    print("\n🔍 Testing API URLs...")
    
    try:
        from apps.embeddings.api_urls import urlpatterns
        print(f"✅ API URLs loaded successfully: {len(urlpatterns)} patterns")
        
        for i, pattern in enumerate(urlpatterns):
            print(f"  {i+1}. {pattern.pattern} -> {pattern.callback.__name__ if hasattr(pattern, 'callback') else 'Router'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading API URLs: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_router():
    """Test if the router is working correctly."""
    print("\n🔍 Testing router...")
    
    try:
        from apps.embeddings.api_views import EmbeddingViewSet, SearchViewSet, SearchLogViewSet
        from rest_framework.routers import DefaultRouter
        
        router = DefaultRouter()
        router.register(r'embeddings', EmbeddingViewSet, basename='embedding')
        router.register(r'search', SearchViewSet, basename='search')
        router.register(r'search-logs', SearchLogViewSet, basename='search-log')
        
        print(f"✅ Router created successfully: {len(router.urls)} URLs")
        
        for url in router.urls:
            print(f"  • {url.pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with router: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_urls():
    """Test if main URLs include API URLs correctly."""
    print("\n🔍 Testing main URL configuration...")
    
    try:
        from config.urls import urlpatterns
        
        # Find API URL pattern
        api_pattern = None
        for pattern in urlpatterns:
            if 'api/v1/' in str(pattern.pattern):
                api_pattern = pattern
                break
        
        if api_pattern:
            print(f"✅ API pattern found: {api_pattern.pattern}")
            print(f"  Include function: {api_pattern.callback}")
            
            # Try to resolve the include
            try:
                included_urls = api_pattern.callback(None, None)
                print(f"✅ Include resolved successfully: {len(included_urls)} patterns")
                return True
            except Exception as e:
                print(f"❌ Error resolving include: {e}")
                return False
        else:
            print("❌ API pattern not found in main URLs")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main URLs: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_django_url_resolution():
    """Test Django URL resolution."""
    print("\n🔍 Testing Django URL resolution...")
    
    try:
        from django.urls import get_resolver
        from django.test import RequestFactory
        
        resolver = get_resolver()
        factory = RequestFactory()
        
        # Test API URLs
        test_urls = [
            '/api/v1/health/',
            '/api/v1/statistics/',
            '/api/v1/auth/token/',
            '/api/v1/embeddings/',
            '/api/v1/search/find_similar/',
        ]
        
        for url in test_urls:
            try:
                request = factory.get(url)
                resolver_match = resolver.resolve(url)
                print(f"✅ {url} -> {resolver_match.view_name}")
            except Exception as e:
                print(f"❌ {url} -> {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in URL resolution: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing API URL Configuration")
    print("=" * 50)
    
    tests = [
        test_api_imports,
        test_api_urls,
        test_router,
        test_main_urls,
        test_django_url_resolution,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! API URLs should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 