"""
Redis service module for embeddings storage and semantic search.

This module provides functions for storing and retrieving embeddings
from Redis Stack for semantic search capabilities with production-grade
features and enhanced error handling.
"""

import logging
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import redis
from redis.commands.search.field import TextField, VectorField
# from redis.commands.search.indexDefinition import IndexDefinition, IndexType  # Comentado por compatibilidad
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from src.config.settings import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Service class for Redis operations with production-grade features."""
    
    def __init__(self):
        """Initialize the Redis service with connection validation."""
        try:
            # Build connection parameters
            connection_params = {
                "host": settings.redis_host,
                "port": int(settings.redis_port),
                "decode_responses": False,  # Keep binary for embeddings
                "socket_connect_timeout": 10,
                "socket_timeout": 10,
                "retry_on_timeout": True,
                "health_check_interval": 30
            }
            
            # Add authentication if provided
            if settings.redis_username:
                connection_params["username"] = settings.redis_username
            if settings.redis_password:
                connection_params["password"] = settings.redis_password
            
            # Add SSL if enabled
            if settings.redis_ssl:
                connection_params["ssl"] = True
                connection_params["ssl_cert_reqs"] = None
            
            self.redis_client = redis.Redis(**connection_params)
            
            # Test connection
            self._validate_connection()
            
            logger.info(f"Redis service initialized successfully. Host: {settings.redis_host}")
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            raise

    def _validate_connection(self) -> None:
        """
        Validate the connection to Redis.
        
        Raises:
            ConnectionError: If connection validation fails
        """
        try:
            # Test connection with ping
            response = self.redis_client.ping()
            if not response:
                raise ConnectionError("Redis ping failed")
            
            # Test basic operations
            test_key = "test_connection"
            self.redis_client.set(test_key, "test_value", ex=10)
            value = self.redis_client.get(test_key)
            if value != b"test_value":
                raise ConnectionError("Redis basic operations test failed")
            
            logger.debug("Redis connection validated successfully")
            
        except Exception as e:
            logger.error(f"Redis connection validation failed: {e}")
            raise

    def store_embedding(
        self, 
        document_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any],
        index_name: str = "document_embeddings",
        expiration_days: int = 30
    ) -> bool:
        """
        Store document embedding with metadata in Redis with enhanced features.
        
        Args:
            document_id: Unique identifier for the document
            embedding: Vector embedding of the document
            metadata: Document metadata (text, filename, etc.)
            index_name: Name of the Redis search index
            expiration_days: Number of days before document expires
            
        Returns:
            bool: True if storage successful
            
        Raises:
            ValueError: If input parameters are invalid
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input parameters
            if not document_id or not embedding:
                raise ValueError("Document ID and embedding cannot be empty")
            
            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError("Embedding must be a non-empty list")
            
            # Create document data with enhanced metadata
            document_data = {
                "document_id": document_id,
                "embedding": pickle.dumps(embedding),  # Serialize embedding
                "text": metadata.get("text", ""),
                "filename": metadata.get("filename", ""),
                "content_type": metadata.get("content_type", ""),
                "upload_date": metadata.get("upload_date", datetime.utcnow().isoformat()),
                "file_size": metadata.get("file_size", 0),
                "processed_date": datetime.utcnow().isoformat(),
                "embedding_dimension": len(embedding)
            }
            
            # Add additional metadata if provided
            for key, value in metadata.items():
                if key not in document_data and isinstance(value, (str, int, float)):
                    document_data[key] = str(value)
            
            # Store in Redis Hash
            key = f"doc:{document_id}"
            self.redis_client.hset(key, mapping=document_data)
            
            # Set expiration
            if expiration_days > 0:
                self.redis_client.expire(key, expiration_days * 24 * 60 * 60)
            
            logger.info(f"Embedding stored successfully for document: {document_id} (dimension: {len(embedding)})")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid input for storing embedding: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error storing embedding for document {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to store embedding for document {document_id}: {e}")
            raise

    def create_search_index(self, index_name: str = "document_embeddings") -> bool:
        """
        Create a Redis search index for semantic search with enhanced schema.
        
        Args:
            index_name: Name of the search index
            
        Returns:
            bool: True if index creation successful
            
        Raises:
            RedisError: If index creation fails
            Exception: For other unexpected errors
        """
        try:
            # Check if index already exists
            try:
                info = self.redis_client.ft(index_name).info()
                logger.info(f"Search index already exists: {index_name}")
                return True
            except:
                pass  # Index doesn't exist, create it
            
            # Define enhanced schema for the index
            schema = (
                TextField("document_id", weight=1.0),
                TextField("text", weight=0.8),
                TextField("filename", weight=0.6),
                TextField("content_type", weight=0.4),
                TextField("upload_date", weight=0.2),
                VectorField(
                    "embedding",
                    "FLOAT32",
                    1536,  # OpenAI ada-002 embedding dimension
                    "FLAT"
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
            
        except RedisError as e:
            logger.error(f"Redis error creating search index {index_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create search index {index_name}: {e}")
            raise

    def semantic_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        index_name: str = "document_embeddings",
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity with enhanced features.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            index_name: Name of the search index
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with metadata
            
        Raises:
            ValueError: If input parameters are invalid
            RedisError: If search operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input parameters
            if not query_embedding or not isinstance(query_embedding, list):
                raise ValueError("Query embedding must be a non-empty list")
            
            if top_k <= 0:
                raise ValueError("top_k must be greater than 0")
            
            if not (0.0 <= similarity_threshold <= 1.0):
                raise ValueError("similarity_threshold must be between 0.0 and 1.0")
            
            # Convert embedding to bytes for Redis
            embedding_bytes = pickle.dumps(query_embedding)
            
            # Build search query with vector similarity
            query = f"*=>[KNN {top_k} @embedding $embedding AS score]"
            query_params = {
                "embedding": embedding_bytes
            }
            
            # Execute search
            results = self.redis_client.ft(index_name).search(
                query,
                query_params=query_params
            )
            
            # Process and filter results
            similar_documents = []
            for doc in results.docs:
                score = float(doc.score)
                
                # Filter by similarity threshold
                if score < similarity_threshold:
                    continue
                
                # Extract document data
                document_data = {
                    "document_id": doc.document_id,
                    "score": score,
                    "text": doc.text,
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "upload_date": doc.upload_date
                }
                
                # Add additional fields if present
                for field_name, field_value in doc.__dict__.items():
                    if field_name not in document_data and not field_name.startswith('_'):
                        document_data[field_name] = field_value
                
                similar_documents.append(document_data)
            
            logger.info(f"Semantic search completed. Found {len(similar_documents)} similar documents")
            return similar_documents
            
        except ValueError as e:
            logger.error(f"Invalid input for semantic search: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error during semantic search: {e}")
            raise
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    def search_similar_documents(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        index_name: str = "document_embeddings",
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Alias for semantic_search for backward compatibility.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            index_name: Name of the search index
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with metadata
        """
        return self.semantic_search(query_embedding, top_k, index_name, similarity_threshold)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID with enhanced error handling.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found
            
        Raises:
            RedisError: If retrieval fails
            Exception: For other unexpected errors
        """
        try:
            key = f"doc:{document_id}"
            document_data = self.redis_client.hgetall(key)
            
            if not document_data:
                logger.info(f"Document not found: {document_id}")
                return None
            
            # Deserialize embedding
            if b"embedding" in document_data:
                try:
                    document_data[b"embedding"] = pickle.loads(document_data[b"embedding"])
                except Exception as e:
                    logger.warning(f"Failed to deserialize embedding for document {document_id}: {e}")
                    document_data[b"embedding"] = None
            
            # Convert bytes to strings for text fields
            result = {}
            for key, value in document_data.items():
                if isinstance(value, bytes) and key != b"embedding":
                    result[key.decode('utf-8')] = value.decode('utf-8')
                else:
                    result[key.decode('utf-8') if isinstance(key, bytes) else key] = value
            
            logger.info(f"Document retrieved successfully: {document_id}")
            return result
            
        except RedisError as e:
            logger.error(f"Redis error retrieving document {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Redis.
        
        Args:
            document_id: Document identifier
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            RedisError: If deletion fails
            Exception: For other unexpected errors
        """
        try:
            key = f"doc:{document_id}"
            result = self.redis_client.delete(key)
            
            if result > 0:
                logger.info(f"Document deleted successfully: {document_id}")
                return True
            else:
                logger.info(f"Document not found for deletion: {document_id}")
                return False
                
        except RedisError as e:
            logger.error(f"Redis error deleting document {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def list_documents(self, pattern: str = "doc:*", limit: int = 100) -> List[str]:
        """
        List document IDs matching a pattern with pagination.
        
        Args:
            pattern: Redis key pattern to match
            limit: Maximum number of documents to return
            
        Returns:
            List[str]: List of document IDs
            
        Raises:
            RedisError: If listing fails
            Exception: For other unexpected errors
        """
        try:
            documents = []
            cursor = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=50)
                documents.extend([key.decode('utf-8').replace('doc:', '') for key in keys])
                
                if cursor == 0 or len(documents) >= limit:
                    break
            
            # Limit results
            documents = documents[:limit]
            
            logger.info(f"Listed {len(documents)} documents matching pattern: {pattern}")
            return documents
            
        except RedisError as e:
            logger.error(f"Redis error listing documents: {e}")
            raise
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
            RedisError: If info retrieval fails
            Exception: For other unexpected errors
        """
        try:
            info = self.redis_client.ft(index_name).info()
            
            # Convert bytes to strings
            result = {}
            for key, value in info.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                result[key] = value
            
            logger.info(f"Retrieved index info for: {index_name}")
            return result
            
        except RedisError as e:
            logger.error(f"Redis error getting index info for {index_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get index info for {index_name}: {e}")
            raise

    def get_document_count(self, index_name: str = "document_embeddings") -> int:
        """
        Get the total number of documents in the index.
        
        Args:
            index_name: Name of the search index
            
        Returns:
            int: Number of documents
            
        Raises:
            RedisError: If count retrieval fails
            Exception: For other unexpected errors
        """
        try:
            info = self.get_index_info(index_name)
            count = int(info.get("num_docs", 0))
            
            logger.info(f"Document count for index {index_name}: {count}")
            return count
            
        except RedisError as e:
            logger.error(f"Redis error getting document count: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            raise

    def health_check(self) -> bool:
        """
        Perform a health check on the Redis connection.
        
        Returns:
            bool: True if Redis is healthy
            
        Raises:
            RedisError: If health check fails
        """
        try:
            # Test basic operations
            test_key = "health_check"
            self.redis_client.set(test_key, "ok", ex=10)
            value = self.redis_client.get(test_key)
            
            if value != b"ok":
                raise RedisError("Health check failed - basic operations not working")
            
            logger.debug("Redis health check passed")
            return True
            
        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            raise

# Global instance for easy access
redis_service = RedisService() 