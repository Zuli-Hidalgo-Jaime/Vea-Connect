# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportCallIssue=false

import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Embedding, EmbeddingSearchLog
from .serializers import (
    EmbeddingSerializer, EmbeddingCreateSerializer, EmbeddingUpdateSerializer,
    SearchQuerySerializer, SearchResponseSerializer, SearchResultSerializer,
    EmbeddingSearchLogSerializer, HealthCheckSerializer, StatisticsSerializer
)
from utilities.embedding_manager import EmbeddingManager, EmbeddingServiceUnavailable

logger = logging.getLogger(__name__)


class EmbeddingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing embeddings.
    
    Provides CRUD operations for embeddings with proper authentication
    and authorization.
    """
    
    queryset = Embedding.objects.all()
    serializer_class = EmbeddingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions and query parameters."""
        queryset = Embedding.objects.all()
        
        # Filter by source type if provided
        source_type = self.request.query_params.get('source_type', None)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Filter by active status
        include_inactive_param = self.request.query_params.get('include_inactive', 'false')
        include_inactive = include_inactive_param.lower() == 'true' if include_inactive_param else False
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.select_related('created_by')
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return EmbeddingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmbeddingUpdateSerializer
        return EmbeddingSerializer
    
    @swagger_auto_schema(
        operation_description="List all embeddings with optional filtering",
        manual_parameters=[
            openapi.Parameter('source_type', openapi.IN_QUERY, description="Filter by source type", type=openapi.TYPE_STRING),
            openapi.Parameter('include_inactive', openapi.IN_QUERY, description="Include inactive embeddings", type=openapi.TYPE_BOOLEAN),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List embeddings with optional filtering."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new embedding",
        request_body=EmbeddingCreateSerializer,
        responses={201: EmbeddingSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Create a new embedding."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        embedding = serializer.save()
        
        logger.info(f"Created embedding {embedding.id} by user {request.user.username}")
        
        response_serializer = EmbeddingSerializer(embedding)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific embedding by ID",
        responses={200: EmbeddingSerializer, 404: "Embedding not found"}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific embedding."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update an embedding",
        request_body=EmbeddingUpdateSerializer,
        responses={200: EmbeddingSerializer, 404: "Embedding not found"}
    )
    def update(self, request, *args, **kwargs):
        """Update an embedding."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update an embedding",
        request_body=EmbeddingUpdateSerializer,
        responses={200: EmbeddingSerializer, 404: "Embedding not found"}
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update an embedding."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete an embedding",
        responses={204: "Embedding deleted successfully", 404: "Embedding not found"}
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an embedding."""
        embedding = self.get_object()
        embedding_id = embedding.id
        
        # Check permissions
        if not request.user.is_staff and embedding.created_by != request.user:
            return Response(
                {"detail": "You do not have permission to delete this embedding."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        embedding.delete()
        logger.info(f"Deleted embedding {embedding_id} by user {request.user.username}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_description="Bulk delete embeddings",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'embedding_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
            }
        ),
        responses={200: "Bulk delete completed", 400: "Invalid request"}
    )
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete embeddings."""
        embedding_ids = request.data.get('embedding_ids', [])
        
        if not embedding_ids:
            return Response(
                {"detail": "No embedding IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter embeddings by user permissions
        queryset = self.get_queryset().filter(id__in=embedding_ids)
        
        if not request.user.is_staff:
            queryset = queryset.filter(created_by=request.user)
        
        deleted_count = queryset.count()
        queryset.delete()
        
        logger.info(f"Bulk deleted {deleted_count} embeddings by user {request.user.username}")
        
        return Response({
            "detail": f"Successfully deleted {deleted_count} embeddings",
            "deleted_count": deleted_count
        })


class SearchViewSet(viewsets.ViewSet):
    """
    ViewSet for semantic search operations.
    
    Provides search functionality using embeddings and similarity matching.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Perform semantic search using embeddings",
        request_body=SearchQuerySerializer,
        responses={200: SearchResponseSerializer, 400: "Invalid search parameters"}
    )
    @action(detail=False, methods=['post'])
    def find_similar(self, request):
        """Perform semantic search to find similar embeddings."""
        start_time = time.time()
        
        # Validate search parameters
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        if not validated_data:
            return Response(
                {"detail": "Invalid search parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = validated_data.get('query', '')
        limit = validated_data.get('limit', 10)
        threshold = validated_data.get('threshold', 0.7)
        source_type = validated_data.get('source_type', '')
        include_inactive = validated_data.get('include_inactive', False)
        
        try:
            # Initialize embedding manager
            embedding_manager = EmbeddingManager()
            
            # Generate embedding for query
            query_embedding = embedding_manager.generate_embedding(query)  # fix: method name without underscore
            
            # Perform search
            search_results = embedding_manager.find_similar(query, top_k=limit)
            
            # Format results
            results = []
            for i, result in enumerate(search_results, 1):
                result_data = {
                    'text': result.get('text', ''),
                    'similarity_score': result.get('similarity', 0.0),
                    'rank': i,
                    'metadata': result.get('metadata', {})
                }
                results.append(result_data)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Log search operation
            try:
                EmbeddingSearchLog.objects.create(
                    query_text=query,
                    query_vector=query_embedding,
                    results_count=len(results),
                    search_time_ms=search_time_ms,
                    user=request.user,
                    metadata={
                        'limit': limit,
                        'threshold': threshold,
                        'source_type': source_type,
                        'include_inactive': include_inactive
                    }
                )
            except Exception as log_error:
                logger.warning(f"Failed to log search: {log_error}")
            
            # Prepare response
            response_data = {
                'query': query,
                'results': results,
                'total_results': len(results),
                'search_time_ms': search_time_ms,
                'limit': limit,
                'threshold': threshold
            }
            
            logger.info(f"Search completed for user {request.user.username}: {len(results)} results in {search_time_ms:.2f}ms")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Search error for user {request.user.username}: {str(e)}")
            return Response(
                {"detail": f"Search failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get search history for the current user",
        manual_parameters=[
            openapi.Parameter('limit', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
        ],
        responses={200: EmbeddingSearchLogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get search history for the current user."""
        limit_param = request.query_params.get('limit', '50')
        try:
            limit = int(limit_param)
        except (ValueError, TypeError):
            limit = 50
        
        searches = EmbeddingSearchLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]
        
        serializer = EmbeddingSearchLogSerializer(searches, many=True)
        return Response(serializer.data)


class HealthCheckView(APIView):
    """
    Ultra-fast health check endpoint for monitoring system status.
    
    Provides minimal health check information with sub-50ms response times.
    No external dependencies to ensure maximum reliability.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Get ultra-fast system health status.
        
        Returns immediately without any external checks.
        
        Returns:
            Response: JSON with health status
        """
        from django.utils import timezone
        
        response_data = {
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'response_time_ms': 0.0
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class StatisticsView(APIView):
    """
    Statistics endpoint for API usage and performance metrics.
    
    Provides comprehensive statistics about embeddings and search operations.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get API usage and performance statistics",
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, description="Number of days for statistics", type=openapi.TYPE_INTEGER),
        ],
        responses={200: StatisticsSerializer}
    )
    def get(self, request):
        """Get API statistics."""
        days = int(request.query_params.get('days', 30))
        since_date = timezone.now() - timedelta(days=days)
        
        # Basic counts
        total_embeddings = Embedding.objects.count()
        active_embeddings = Embedding.objects.filter(is_active=True).count()
        
        # Search statistics
        recent_searches = EmbeddingSearchLog.objects.filter(
            created_at__gte=since_date
        )
        total_searches = recent_searches.count()
        
        # Average search time
        avg_search_time = recent_searches.aggregate(
            avg_time=Avg('search_time_ms')
        )['avg_time'] or 0.0
        
        # Embeddings by source type
        embeddings_by_source_type = Embedding.objects.values('source_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        source_type_dict = {item['source_type']: item['count'] for item in embeddings_by_source_type}
        
        # Recent search queries
        recent_queries = recent_searches.values_list('query_text', flat=True)[:10]
        
        # Top searched terms (simplified)
        top_terms = recent_searches.values_list('query_text', flat=True)[:5]
        
        response_data = {
            'total_embeddings': total_embeddings,
            'active_embeddings': active_embeddings,
            'total_searches': total_searches,
            'average_search_time': avg_search_time,
            'embeddings_by_source_type': source_type_dict,
            'recent_searches': list(recent_queries),
            'top_searched_terms': list(top_terms),
        }
        
        return Response(response_data)


class SearchLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing search logs.
    
    Provides read-only access to search log entries.
    """
    
    serializer_class = EmbeddingSearchLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter search logs by user permissions."""
        queryset = EmbeddingSearchLog.objects.all()
        
        # Non-staff users can only see their own searches
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user').order_by('-created_at') 