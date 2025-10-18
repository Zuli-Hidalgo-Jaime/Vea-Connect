from rest_framework import serializers
from .models import Embedding, EmbeddingSearchLog
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class EmbeddingSerializer(serializers.ModelSerializer):
    """
    Serializer for Embedding model.
    
    Handles serialization and deserialization of embedding data
    for API operations.
    """
    
    created_by = UserSerializer(read_only=True)
    vector_dimension = serializers.ReadOnlyField(source='get_vector_dimension')
    text_preview = serializers.ReadOnlyField(source='get_text_preview')
    
    class Meta:
        model = Embedding
        fields = [
            'id', 'text', 'embedding_vector', 'metadata', 'source_type',
            'source_id', 'created_by', 'created_at', 'updated_at',
            'is_active', 'vector_dimension', 'text_preview'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'vector_dimension', 'text_preview']
    
    def create(self, validated_data):
        """Create a new embedding with the current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_embedding_vector(self, value):
        """Validate that embedding_vector is a list of numbers."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Embedding vector must be a list")
        
        if not all(isinstance(x, (int, float)) for x in value):
            raise serializers.ValidationError("All elements in embedding vector must be numbers")
        
        return value
    
    def validate_metadata(self, value):
        """Validate that metadata is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a dictionary")
        return value


class EmbeddingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating embeddings.
    
    Simplified serializer for creation operations.
    """
    
    class Meta:
        model = Embedding
        fields = ['text', 'embedding_vector', 'metadata', 'source_type', 'source_id']
    
    def validate_embedding_vector(self, value):
        """Validate that embedding_vector is a list of numbers."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Embedding vector must be a list")
        
        if not all(isinstance(x, (int, float)) for x in value):
            raise serializers.ValidationError("All elements in embedding vector must be numbers")
        
        return value


class EmbeddingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating embeddings.
    
    Allows partial updates of embedding fields.
    """
    
    class Meta:
        model = Embedding
        fields = ['text', 'embedding_vector', 'metadata', 'source_type', 'source_id', 'is_active']
    
    def validate_embedding_vector(self, value):
        """Validate that embedding_vector is a list of numbers."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Embedding vector must be a list")
        
        if not all(isinstance(x, (int, float)) for x in value):
            raise serializers.ValidationError("All elements in embedding vector must be numbers")
        
        return value


class SearchQuerySerializer(serializers.Serializer):
    """
    Serializer for search query parameters.
    
    Handles validation of search query input.
    """
    
    query = serializers.CharField(max_length=1000, help_text="Search query text")
    limit = serializers.IntegerField(default=10, min_value=1, max_value=100, help_text="Maximum number of results")
    threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0, help_text="Similarity threshold")
    source_type = serializers.CharField(required=False, allow_blank=True, help_text="Filter by source type")
    include_inactive = serializers.BooleanField(default=False, help_text="Include inactive embeddings")
    
    def validate_query(self, value):
        """Validate that query is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Query cannot be empty")
        return value.strip()


class SearchResultSerializer(serializers.Serializer):
    """
    Serializer for search results.
    
    Represents a single search result with similarity score.
    """
    
    embedding = EmbeddingSerializer()
    similarity_score = serializers.FloatField(help_text="Similarity score between query and embedding")
    rank = serializers.IntegerField(help_text="Rank position in search results")


class SearchResponseSerializer(serializers.Serializer):
    """
    Serializer for search response.
    
    Contains search results and metadata.
    """
    
    query = serializers.CharField(help_text="Original search query")
    results = SearchResultSerializer(many=True, help_text="Search results")
    total_results = serializers.IntegerField(help_text="Total number of results found")
    search_time_ms = serializers.FloatField(help_text="Search execution time in milliseconds")
    limit = serializers.IntegerField(help_text="Maximum number of results requested")
    threshold = serializers.FloatField(help_text="Similarity threshold used")


class EmbeddingSearchLogSerializer(serializers.ModelSerializer):
    """
    Serializer for EmbeddingSearchLog model.
    
    Handles serialization of search log entries.
    """
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EmbeddingSearchLog
        fields = [
            'id', 'query_text', 'query_vector', 'results_count',
            'search_time_ms', 'user', 'created_at', 'metadata'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer for health check response.
    
    Provides system health status information.
    """
    
    status = serializers.CharField(help_text="Overall system status")
    timestamp = serializers.DateTimeField(help_text="Health check timestamp")
    services = serializers.DictField(help_text="Status of individual services")
    version = serializers.CharField(help_text="API version")
    uptime = serializers.FloatField(help_text="System uptime in seconds")


class StatisticsSerializer(serializers.Serializer):
    """
    Serializer for API statistics.
    
    Provides usage and performance statistics.
    """
    
    total_embeddings = serializers.IntegerField(help_text="Total number of embeddings")
    active_embeddings = serializers.IntegerField(help_text="Number of active embeddings")
    total_searches = serializers.IntegerField(help_text="Total number of searches performed")
    average_search_time = serializers.FloatField(help_text="Average search time in milliseconds")
    embeddings_by_source_type = serializers.DictField(help_text="Embeddings count by source type")
    recent_searches = serializers.ListField(help_text="Recent search queries")
    top_searched_terms = serializers.ListField(help_text="Most searched terms") 