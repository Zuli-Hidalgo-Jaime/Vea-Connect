from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Embedding(models.Model):
    """
    Model for storing text embeddings with metadata.
    
    This model stores embeddings generated from text content along with
    metadata for search and retrieval purposes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(help_text="Original text content that was embedded")
    embedding_vector = models.JSONField(help_text="Vector representation of the text")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata for the embedding")
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('document', 'Document'),
            ('event', 'Event'),
            ('contact', 'Contact'),
            ('donation', 'Donation'),
            ('custom', 'Custom'),
        ],
        default='custom',
        help_text="Type of source content"
    )
    source_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID of the source object (document, event, etc.)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='embeddings_created',
        help_text="User who created this embedding"
    )
    created_at = models.DateTimeField(default=timezone.now, help_text="Creation timestamp")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")
    is_active = models.BooleanField(default=True, help_text="Whether this embedding is active")
    
    class Meta:
        db_table = 'embeddings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Embedding"
        verbose_name_plural = "Embeddings"
    
    def __str__(self):
        """String representation of the embedding."""
        return f"Embedding {self.id} - {self.source_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_text_preview(self):
        """Get a preview of the text content."""
        return self.text[:100] + "..." if len(self.text) > 100 else self.text
    
    def get_vector_dimension(self):
        """Get the dimension of the embedding vector."""
        if isinstance(self.embedding_vector, list):
            return len(self.embedding_vector)
        return 0
    
    def to_dict(self):
        """Convert the embedding to a dictionary representation."""
        return {
            'id': str(self.id),
            'text': self.text,
            'embedding_vector': self.embedding_vector,
            'metadata': self.metadata,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'created_by': self.created_by.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'vector_dimension': self.get_vector_dimension(),
        }


class EmbeddingSearchLog(models.Model):
    """
    Model for logging embedding search operations.
    
    This model tracks search queries and results for analytics and debugging.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.TextField(help_text="Search query text")
    query_vector = models.JSONField(help_text="Vector representation of the query")
    results_count = models.IntegerField(default=0, help_text="Number of results returned")
    search_time_ms = models.FloatField(default=0.0, help_text="Search execution time in milliseconds")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='embedding_searches',
        help_text="User who performed the search"
    )
    created_at = models.DateTimeField(default=timezone.now, help_text="Search timestamp")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional search metadata")
    
    class Meta:
        db_table = 'embedding_search_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['results_count']),
        ]
        verbose_name = "Embedding Search Log"
        verbose_name_plural = "Embedding Search Logs"
    
    def __str__(self):
        """String representation of the search log."""
        return f"Search {self.id} - {self.query_text[:50]}... ({self.created_at.strftime('%Y-%m-%d %H:%M')})" 