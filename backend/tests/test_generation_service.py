from unittest.mock import MagicMock, PropertyMock, patch
import pytest
from google.genai import errors

from backend.app.schemas.query import SourceReference
from backend.app.services.generation_service import GenerationService


@pytest.fixture
def mock_generation_service():
    service = GenerationService(api_key="mock_key", model_name="gemini-3.7-flash")
    return service


def test_empty_context_grounding(mock_generation_service):
    """Verify empty context returns grounded 'not found' message without calling LLM."""
    sources = [SourceReference(document="test.pdf", page=1, score=0.9)]
    result = mock_generation_service.generate_answer(
        question="What is the budget?",
        context="",
        sources=sources,
    )

    assert result.answer == "I could not find relevant information in the uploaded documents to answer your question."
    assert result.sources == []


def test_successful_answer_generation(mock_generation_service):
    """Verify answer generation when valid context is provided."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "The total budget allocated is $1,000,000."
    mock_client.models.generate_content.return_value = mock_response

    sources = [SourceReference(document="budget.pdf", page=2, score=0.95)]
    context = "[budget.pdf | Page 2]\nTotal project budget is $1,000,000."

    with patch.object(GenerationService, "client", new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_client
        result = mock_generation_service.generate_answer(
            question="What is the budget?",
            context=context,
            sources=sources,
        )

    assert result.answer == "The total budget allocated is $1,000,000."
    assert len(result.sources) == 1
    assert result.sources[0].document == "budget.pdf"


def test_gemini_api_error_retry_and_wrapping(mock_generation_service):
    """Verify API errors retry transient errors and wrap exceptions per Spec 12.3/12.4."""
    mock_client = MagicMock()
    try:
        api_error_inst = errors.APIError(503, "Service Unavailable", {})
    except Exception:
        api_error_inst = errors.APIError("Service Unavailable")

    mock_client.models.generate_content.side_effect = api_error_inst

    context = "[doc.txt | Page 1]\nSample context"

    with patch.object(GenerationService, "client", new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_client
        with pytest.raises(RuntimeError) as exc_info:
            mock_generation_service.generate_answer(
                question="What is this?",
                context=context,
                sources=[],
                max_retries=2,
            )

    assert "unavailable" in str(exc_info.value).lower()

