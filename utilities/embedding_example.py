"""
Example usage of EmbeddingManager.

This module demonstrates how to use the EmbeddingManager for various
embedding operations including CRUD and similarity search.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utilities.embedding_manager import EmbeddingManager


def example_basic_operations():
    """Example of basic CRUD operations."""
    print("=== Basic CRUD Operations Example ===")
    
    # Get embedding manager
    manager = EmbeddingManager()
    
    # Example document data
    document_id = "example-doc-001"
    text = """
    Python is a high-level, interpreted programming language known for its 
    simplicity and readability. It supports multiple programming paradigms 
    including procedural, object-oriented, and functional programming.
    """
    metadata = {
        "title": "Introduction to Python",
        "author": "Example Author",
        "category": "programming",
        "tags": ["python", "programming", "tutorial"]
    }
    
    # Create embedding
    print("1. Creating embedding...")
    success = manager.create_embedding(document_id, text, metadata)
    print(f"   Result: {'Success' if success else 'Failed'}")
    
    # Get embedding
    print("\n2. Retrieving embedding...")
    data = manager.get_embedding(document_id)
    if data:
        print(f"   Document ID: {data['document_id']}")
        print(f"   Text length: {len(data['text'])} characters")
        print(f"   Embedding dimensions: {len(data['embedding'])}")
        print(f"   Metadata: {data['metadata']}")
    
    # Update embedding
    print("\n3. Updating embedding...")
    updated_text = """
    Python is a versatile programming language that emphasizes code readability 
    and simplicity. It's widely used in web development, data science, 
    artificial intelligence, and automation.
    """
    updated_metadata = {
        "title": "Python Programming Language",
        "author": "Example Author",
        "category": "programming",
        "tags": ["python", "programming", "web development", "data science"],
        "version": "2.0"
    }
    
    update_success = manager.update_embedding(document_id, updated_text, updated_metadata)
    print(f"   Result: {'Success' if update_success else 'Failed'}")
    
    # Check existence
    print("\n4. Checking existence...")
    exists = manager.exists(document_id)
    print(f"   Exists: {exists}")
    
    # Delete embedding
    print("\n5. Deleting embedding...")
    delete_success = manager.delete_embedding(document_id)
    print(f"   Result: {'Success' if delete_success else 'Failed'}")
    
    # Verify deletion
    final_check = manager.exists(document_id)
    print(f"   Final existence check: {final_check}")


def example_multiple_documents():
    """Example with multiple documents."""
    print("\n=== Multiple Documents Example ===")
    
    manager = EmbeddingManager()
    
    # Create multiple documents
    documents = [
        {
            "id": "doc-001",
            "text": "Machine learning is a subset of artificial intelligence.",
            "metadata": {"category": "AI", "topic": "machine learning"}
        },
        {
            "id": "doc-002", 
            "text": "Deep learning uses neural networks with multiple layers.",
            "metadata": {"category": "AI", "topic": "deep learning"}
        },
        {
            "id": "doc-003",
            "text": "Natural language processing helps computers understand human language.",
            "metadata": {"category": "AI", "topic": "NLP"}
        }
    ]
    
    print("Creating multiple documents...")
    for doc in documents:
        success = manager.create_embedding(doc["id"], doc["text"], doc["metadata"])
        print(f"   {doc['id']}: {'Success' if success else 'Failed'}")
    
    # Get statistics
    print("\nGetting statistics...")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


def example_similarity_search():
    """Example of similarity search (dummy implementation)."""
    print("\n=== Similarity Search Example ===")
    
    manager = EmbeddingManager()
    
    # Create a test document first
    test_doc_id = "similarity-test-doc"
    test_text = "Artificial intelligence and machine learning are transforming technology."
    test_metadata = {"category": "technology", "topic": "AI/ML"}
    
    manager.create_embedding(test_doc_id, test_text, test_metadata)
    
    # Perform similarity search
    queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Tell me about technology trends"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = manager.find_similar(query, top_k=3)
        
        if results:
            print(f"   Found {len(results)} similar documents:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['document_id']} (similarity: {result['similarity_score']:.4f})")
        else:
            print("   No similar documents found (expected with dummy implementation)")
    
    # Cleanup
    manager.delete_embedding(test_doc_id)


def example_error_handling():
    """Example of error handling."""
    print("\n=== Error Handling Example ===")
    
    manager = EmbeddingManager()
    
    # Try to get non-existent document
    print("1. Getting non-existent document...")
    data = manager.get_embedding("non-existent-doc")
    print(f"   Result: {data}")
    
    # Try to update non-existent document
    print("\n2. Updating non-existent document...")
    success = manager.update_embedding("non-existent-doc", "new text", {})
    print(f"   Result: {'Success' if success else 'Failed'}")
    
    # Try to delete non-existent document
    print("\n3. Deleting non-existent document...")
    success = manager.delete_embedding("non-existent-doc")
    print(f"   Result: {'Success' if success else 'Failed'}")


def main():
    """Main example function."""
    print("EmbeddingManager Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_operations()
        example_multiple_documents()
        example_similarity_search()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 