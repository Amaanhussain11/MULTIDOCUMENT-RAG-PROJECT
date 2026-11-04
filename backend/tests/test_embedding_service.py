"""Unit tests for EmbeddingService including rate-limit 429 recovery."""

from unittest.mock import MagicMock, patch

from google.genai import errors

from backend.app.services.embedding_service import EmbeddingService


def test_embed_empty_texts_returns_empty():
    service = EmbeddingService(api_key="test_key")
    assert service.embed_texts([]) == []


def test_embed_batch_success():
    service = EmbeddingService(api_key="test_key")
    mock_client = MagicMock()

    mock_item_1 = MagicMock()
    mock_item_1.values = [0.1, 0.2, 0.3]
    mock_item_2 = MagicMock()
    mock_item_2.values = [0.4, 0.5, 0.6]

    mock_response = MagicMock()
    mock_response.embeddings = [mock_item_1, mock_item_2]
    mock_client.models.embed_content.return_value = mock_response
    service._client = mock_client

    results = service.embed_texts(["text1", "text2"], batch_size=5)
    assert len(results) == 2
    assert results[0] == [0.1, 0.2, 0.3]
    assert results[1] == [0.4, 0.5, 0.6]


@patch("time.sleep", return_value=None)
def test_embed_rate_limit_429_auto_retry(mock_sleep):
    service = EmbeddingService(api_key="test_key")
    mock_client = MagicMock()

    # Attempt 1: 429 Quota Exceeded error
    err_json = {
        "error": {
            "code": 429,
            "message": "Resource exhausted. Please retry in 50.0s.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "50s",
                }
            ],
        }
    }
    rate_limit_err = errors.APIError(429, err_json)

    # Attempt 2: Success
    mock_item = MagicMock()
    mock_item.values = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.embeddings = [mock_item]

    mock_client.models.embed_content.side_effect = [rate_limit_err, mock_response]
    service._client = mock_client

    results = service.embed_texts(["sample long text chunk"], batch_size=5)
    assert len(results) == 1
    assert results[0] == [0.1, 0.2, 0.3]

    # Verify sleep was called with parsed delay (~52s)
    assert mock_sleep.called
    slept_time = mock_sleep.call_args[0][0]
    assert slept_time >= 50.0
