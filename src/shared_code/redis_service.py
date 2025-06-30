"""
Redis service module for embeddings storage and semantic search.

This module provides functions for storing and retrieving embeddings
from Redis Stack for semantic search capabilities.
"""

import logging
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
import redis
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from src.config.settings import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Service class for Redis operations."""
    
    def __init__(self):
        """Initialize the Redis service."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=int(settings.redis_port),
                username=settings.redis_username if settings.redis_username else None,
                password=settings.redis_password if settings.redis_password else None,
                ssl=settings.redis_ssl,
                decode_responses=False  # Keep binary for embeddings
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis service initialized successfully. Host: {settings.redis_host}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            raise

    def store_embedding(
        self, 
        document_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any],
        index_name: str = "document_embeddings"
    ) -> bool:
        """
        Store document embedding with metadata in Redis.
        
        Args:
            document_id: Unique identifier for the document
            embedding: Vector embedding of the document
            metadata: Document metadata (text, filename, etc.)
            index_name: Name of the Redis search index
            
        Returns:
            bool: True if storage successful
            
        Raises:
            Exception: If storage fails
        """
        try:
            # Create document data
            document_data = {
                "document_id": document_id,
                "embedding": pickle.dumps(embedding),  # Serialize embedding
                "text": metadata.get("text", ""),
                "filename": metadata.get("filename", ""),
                "content_type": metadata.get("content_type", ""),
                "upload_date": metadata.get("upload_date", ""),
                "file_size": metadata.get("file_size", 0)
            }
            
            # Store in Redis Hash
            key = f"doc:{document_id}"
            self.redis_client.hset(key, mapping=document_data)
            
            # Set expiration (optional, e.g., 30 days)
            self.redis_client.expire(key, 30 * 24 * 60 * 60)
            
            logger.info(f"Embedding stored successfully for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding for document {document_id}: {e}")
            raise

    def create_search_index(self, index_name: str = "document_embeddings") -> bool:
        """
        Create a Redis search index for semantic search.
        
        Args:
            index_name: Name of the search index
            
        Returns:
            bool: True if index creation successful
            
        Raises:
            Exception: If index creation fails
        """
        try:
            # Define schema for the index
            schema = (
                TextField("document_id"),
                TextField("text"),
                TextField("filename"),
                TextField("content_type"),
                TextField("upload_date"),
                VectorField(
                    "embedding",
                    "FLOAT32",
                    1536,  # OpenAI ada-002 embedding dimension
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 1536,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            
            # Create the index
            self.redis_client.ft(index_name).create_index(
                schema,
                definition=IndexDefinition(
                    prefix=["doc:"],
                    index_type=IndexType.HASH
                )
            )
            
            logger.info(f"Search index created successfully: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create search index {index_name}: {e}")
            raise

    def semantic_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        index_name: str = "document_embeddings"
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to return
            index_name: Name of the search index
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with scores
            
        Raises:
            Exception: If search fails
        """
        try:
            # Prepare query
            query_vector = pickle.dumps(query_embedding)
            query = f"*=>[KNN {top_k} @embedding $query_vector AS score]"
            
            # Execute search
            results = self.redis_client.ft(index_name).search(
                query,
                query_params={
                    "query_vector": query_vector
                },
                sort_by="score",
                return_fields=["document_id", "text", "filename", "content_type", "score"]
            )
            
            # Process results
            search_results = []
            for doc in results.docs:
                result = {
                    "document_id": doc.document_id,
                    "text": doc.text,
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "score": float(doc.score)
                }
                search_results.append(result)
            
            logger.info(f"Semantic search completed. Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[Dict[str, Any]]: Document data if found, None otherwise
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            key = f"doc:{document_id}"
            document_data = self.redis_client.hgetall(key)
            
            if not document_data:
                logger.warning(f"Document not found: {document_id}")
                return None
            
            # Deserialize embedding
            embedding = pickle.loads(document_data[b"embedding"])
            
            document = {
                "document_id": document_data[b"document_id"].decode("utf-8"),
                "text": document_data[b"text"].decode("utf-8"),
                "filename": document_data[b"filename"].decode("utf-8"),
                "content_type": document_data[b"content_type"].decode("utf-8"),
                "upload_date": document_data[b"upload_date"].decode("utf-8"),
                "file_size": int(document_data[b"file_size"]),
                "embedding": embedding
            }
            
            logger.info(f"Document retrieved successfully: {document_id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Redis.
        
        Args:
            document_id: Document identifier to delete
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            Exception: If deletion fails
        """
        try:
            key = f"doc:{document_id}"
            result = self.redis_client.delete(key)
            
            if result:
                logger.info(f"Document deleted successfully: {document_id}")
                return True
            else:
                logger.warning(f"Document not found for deletion: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def list_documents(self, pattern: str = "doc:*") -> List[str]:
        """
        List all document IDs in Redis.
        
        Args:
            pattern: Redis key pattern to match
            
        Returns:
            List[str]: List of document IDs
            
        Raises:
            Exception: If listing fails
        """
        try:
            keys = self.redis_client.keys(pattern)
            document_ids = [key.decode("utf-8").replace("doc:", "") for key in keys]
            
            logger.info(f"Listed {len(document_ids)} documents")
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise

    def get_index_info(self, index_name: str = "document_embeddings") -> Dict[str, Any]:
        """
        Get information about a search index.
        
        Args:
            index_name: Name of the search index
            
        Returns:
            Dict[str, Any]: Index information
            
        Raises:
            Exception: If info retrieval fails
        """
        try:
            info = self.redis_client.ft(index_name).info()
            
            index_info = {
                "index_name": index_name,
                "num_docs": info.get("num_docs", 0),
                "inverted_sz_mb": info.get("inverted_sz_mb", 0),
                "vector_index_sz_mb": info.get("vector_index_sz_mb", 0),
                "total_inverted_index_blocks": info.get("total_inverted_index_blocks", 0)
            }
            
            logger.info(f"Index info retrieved for {index_name}")
            return index_info
            
        except Exception as e:
            logger.error(f"Failed to get index info for {index_name}: {e}")
            raise

# Global instance for easy access
redis_service = RedisService() 