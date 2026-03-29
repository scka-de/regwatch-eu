"""Tests for LLM classification abstraction."""

from unittest.mock import MagicMock, patch

from regwatch.classifier import create_llm_classifier, detect_llm_provider


def test_detect_provider_claude():
    assert detect_llm_provider("sk-ant-abc123") == "claude"


def test_detect_provider_openai():
    assert detect_llm_provider("sk-abc123") == "openai"


def test_detect_provider_none():
    assert detect_llm_provider(None) is None


def test_detect_provider_empty():
    assert detect_llm_provider("") is None


def test_create_llm_classifier_returns_callable():
    fn = create_llm_classifier("sk-ant-test123")
    assert callable(fn)


def test_create_llm_classifier_none_key():
    assert create_llm_classifier(None) is None


@patch("regwatch.classifier.httpx.post")
def test_llm_classifier_claude_call(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": '{"regulation": "dora"}'}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    fn = create_llm_classifier("sk-ant-test123")
    result = fn("Some DORA title", "Description about ICT risk")
    assert result == "dora"


@patch("regwatch.classifier.httpx.post")
def test_llm_classifier_openai_call(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"regulation": "mica"}'}}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    fn = create_llm_classifier("sk-test123")
    result = fn("MiCA related title", "Crypto regulation")
    assert result == "mica"


@patch("regwatch.classifier.httpx.post")
def test_llm_classifier_handles_invalid_json(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": "not valid json"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    fn = create_llm_classifier("sk-ant-test123")
    result = fn("Title", "Description")
    assert result is None


@patch("regwatch.classifier.httpx.post")
def test_llm_classifier_handles_http_error(mock_post):
    import httpx

    mock_post.side_effect = httpx.HTTPError("Server error")
    fn = create_llm_classifier("sk-ant-test123")
    result = fn("Title", "Description")
    assert result is None


@patch("regwatch.classifier.httpx.post")
def test_llm_classifier_other_regulation_returns_none(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": '{"regulation": "other"}'}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    fn = create_llm_classifier("sk-ant-test123")
    result = fn("Fishing quotas", "Not a fintech regulation")
    assert result is None
