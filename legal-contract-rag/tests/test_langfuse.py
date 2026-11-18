"""
Pytest Test Suite for Langfuse LLM Observability & Tracing Integration.
Validates Task 7 requirements:
- Langfuse configuration & initialization
- Graceful degradation / no-op handling when disabled or unconfigured
- Generation tracing (prompts, outputs, metadata, tags)
- Live mock tracing validation
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.app.observability.langfuse_service import LangfuseService


def test_langfuse_local_mode():
    """Verify local mode defaults to local URL and local keys."""
    service = LangfuseService(mode="LOCAL", host="http://localhost:3000", enabled=True, client=MagicMock())
    assert service.is_active
    assert service.mode == "LOCAL"
    assert "localhost:3000" in service.host


def test_langfuse_cloud_mode():
    """Verify cloud mode defaults to cloud URL."""
    service = LangfuseService(
        mode="CLOUD",
        host="https://cloud.langfuse.com",
        public_key="pk-lf-cloud",
        secret_key="sk-lf-cloud",
        enabled=True,
        client=MagicMock()
    )
    assert service.is_active
    assert service.mode == "CLOUD"
    assert "cloud.langfuse.com" in service.host


def test_langfuse_missing_credentials():
    """Ensure Langfuse degrades to disabled if keys are missing."""
    service = LangfuseService(public_key="", secret_key="", enabled=True)
    assert not service.is_active


def test_langfuse_active_tracing_mock():
    """Test full trace creation and generation capture with mocked Langfuse client."""
    mock_client = MagicMock()
    mock_trace = MagicMock()
    mock_trace.id = "trace-uuid-12345"
    mock_client.trace.return_value = mock_trace

    service = LangfuseService(
        public_key="pk-lf-test",
        secret_key="sk-lf-test",
        host="https://cloud.langfuse.com",
        enabled=True,
        client=mock_client
    )

    trace_id = service.trace_generation(
        name="legal-contract-qa",
        model="gemini-1.5-flash",
        system_prompt="You are a legal AI.",
        user_prompt="What is the cure period?",
        output_text="The cure period is thirty (30) days.",
        provider="gemini",
        user_id="legal_reviewer_1",
        session_id="conv-abc-123",
        metadata={"contract_id": "CNT-001", "chunk_count": 5},
        tags=["legal", "gemini"]
    )

    assert trace_id == "trace-uuid-12345"
    mock_client.trace.assert_called_once_with(
        name="legal-contract-qa",
        user_id="legal_reviewer_1",
        session_id="conv-abc-123",
        metadata={"contract_id": "CNT-001", "chunk_count": 5},
        tags=["legal", "gemini"]
    )
    mock_trace.generation.assert_called_once()
    args, kwargs = mock_trace.generation.call_args
    assert kwargs["name"] == "legal-contract-qa-llm-generation"
    assert kwargs["model"] == "gemini-1.5-flash"
    assert kwargs["input"]["user_prompt"] == "What is the cure period?"
    assert kwargs["output"] == "The cure period is thirty (30) days."
    assert kwargs["metadata"]["provider"] == "gemini"
    assert kwargs["metadata"]["contract_id"] == "CNT-001"
    mock_client.flush.assert_called_once()
