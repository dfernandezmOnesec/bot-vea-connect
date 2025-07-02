"""
Unit tests for Redis service module.

This module contains comprehensive tests for the RedisService class
with mocked Redis client and full coverage of all methods.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from shared_code.redis_service import RedisService

class TestRedisService:
    """Test cases for RedisService class."""

    @pytest.fixture
    def mock_settings_env(self):
        with patch('src.shared_code.redis_service.settings') as mock_settings:
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.redis_username = ""
            mock_settings.redis_password = ""
            mock_settings.redis_ssl = False
            yield mock_settings

    @pytest.fixture
    def mock_redis(self):
        with patch('src.shared_code.redis_service.redis.Redis') as mock_redis:
            yield mock_redis

    @pytest.fixture
    def redis_service(self, mock_settings_env, mock_redis):
        # Mock the Redis client creation and validation
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_client.get.return_value = b"test_value"
        mock_redis.return_value = mock_client
        
        with patch('src.shared_code.redis_service.RedisService._validate_connection'):
            service = RedisService()
            return service

    def test_store_embedding_success(self, redis_service):
        redis_service.redis_client.hset.return_value = True
        redis_service.redis_client.expire.return_value = True
        result = redis_service.store_embedding(
            document_id="doc1",
            embedding=[0.1, 0.2, 0.3],
            metadata={"text": "test", "filename": "file.txt"}
        )
        assert result is True

    def test_store_embedding_invalid_input(self, redis_service):
        with pytest.raises(ValueError):
            redis_service.store_embedding(document_id="", embedding=[], metadata={})

    def test_store_embedding_redis_error(self, redis_service):
        redis_service.redis_client.hset.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.store_embedding(document_id="doc1", embedding=[1.0], metadata={})

    def test_create_search_index_success(self, redis_service):
        redis_service.redis_client.ft.return_value.info.side_effect = Exception()
        redis_service.redis_client.ft.return_value.create_index.return_value = True
        result = redis_service.create_search_index(index_name="test_index")
        assert result is True

    def test_create_search_index_already_exists(self, redis_service):
        redis_service.redis_client.ft.return_value.info.return_value = {"num_docs": 1}
        result = redis_service.create_search_index(index_name="test_index")
        assert result is True

    def test_create_search_index_redis_error(self, redis_service):
        redis_service.redis_client.ft.return_value.create_index.side_effect = RedisError("Redis error")
        redis_service.redis_client.ft.return_value.info.side_effect = Exception()
        with pytest.raises(RedisError):
            redis_service.create_search_index(index_name="test_index")

    def test_semantic_search_success(self, redis_service):
        mock_doc = Mock()
        mock_doc.document_id = "doc1"
        mock_doc.text = "test"
        mock_doc.filename = "file.txt"
        mock_doc.content_type = "text/plain"
        mock_doc.score = 0.9
        mock_doc.upload_date = "2024-01-01"
        redis_service.redis_client.ft.return_value.search.return_value.docs = [mock_doc]
        result = redis_service.semantic_search([0.1, 0.2, 0.3], top_k=1, similarity_threshold=0.7)
        assert isinstance(result, list)
        assert result[0]["document_id"] == "doc1"

    def test_semantic_search_invalid_input(self, redis_service):
        with pytest.raises(ValueError):
            redis_service.semantic_search([], top_k=1)
        with pytest.raises(ValueError):
            redis_service.semantic_search([0.1], top_k=1, similarity_threshold=2.0)

    def test_semantic_search_redis_error(self, redis_service):
        redis_service.redis_client.ft.return_value.search.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.semantic_search([0.1, 0.2, 0.3], top_k=1)

    def test_get_document_success(self, redis_service):
        redis_service.redis_client.hgetall.return_value = {
            b"document_id": b"doc1",
            b"text": b"test",
            b"filename": b"file.txt",
            b"content_type": b"text/plain",
            b"upload_date": b"2024-01-01",
            b"embedding": b"\x80\x03]q\x00(G?\x9a\x99\x99\x99\x99\x99\xb9?\x9a\x99\x99\x99\x99\x99\xc9@e."
        }
        result = redis_service.get_document("doc1")
        assert result["document_id"] == "doc1"
        assert result["text"] == "test"

    def test_get_document_not_found(self, redis_service):
        redis_service.redis_client.hgetall.return_value = {}
        result = redis_service.get_document("doc2")
        assert result is None

    def test_get_document_redis_error(self, redis_service):
        redis_service.redis_client.hgetall.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.get_document("doc1")

    def test_delete_document_success(self, redis_service):
        redis_service.redis_client.delete.return_value = 1
        result = redis_service.delete_document("doc1")
        assert result is True

    def test_delete_document_not_found(self, redis_service):
        redis_service.redis_client.delete.return_value = 0
        result = redis_service.delete_document("doc2")
        assert result is False

    def test_delete_document_redis_error(self, redis_service):
        redis_service.redis_client.delete.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.delete_document("doc1")

    def test_list_documents_success(self, redis_service):
        redis_service.redis_client.scan.side_effect = [
            (1, [b"doc:1", b"doc:2"]),
            (0, [b"doc:3"])
        ]
        result = redis_service.list_documents(pattern="doc:*", limit=10)
        assert result == ["1", "2", "3"]

    def test_list_documents_redis_error(self, redis_service):
        redis_service.redis_client.scan.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.list_documents()

    def test_get_index_info_success(self, redis_service):
        redis_service.redis_client.ft.return_value.info.return_value = {b"num_docs": b"3"}
        result = redis_service.get_index_info()
        assert result["num_docs"] == "3"

    def test_get_index_info_redis_error(self, redis_service):
        redis_service.redis_client.ft.return_value.info.side_effect = RedisError("Redis error")
        with pytest.raises(RedisError):
            redis_service.get_index_info()

    def test_get_document_count_success(self, redis_service):
        with patch.object(redis_service, 'get_index_info', return_value={"num_docs": 5}):
            result = redis_service.get_document_count()
            assert result == 5

    def test_get_document_count_redis_error(self, redis_service):
        with patch.object(redis_service, 'get_index_info', side_effect=RedisError("Redis error")):
            with pytest.raises(RedisError):
                redis_service.get_document_count()

    def test_health_check_success(self, redis_service):
        redis_service.redis_client.set.return_value = True
        redis_service.redis_client.get.return_value = b"ok"
        result = redis_service.health_check()
        assert result is True

    def test_health_check_fail(self, redis_service):
        redis_service.redis_client.set.return_value = True
        redis_service.redis_client.get.return_value = None
        with pytest.raises(RedisError):
            redis_service.health_check() 