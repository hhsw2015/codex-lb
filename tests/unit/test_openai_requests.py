from __future__ import annotations

import pytest

from app.core.openai.requests import ResponsesRequest


def test_messages_convert_to_responses_input():
    payload = {
        "model": "gpt-5.1",
        "messages": [{"role": "user", "content": "hi"}],
    }
    request = ResponsesRequest.model_validate(payload)

    assert request.instructions == ""
    assert request.input == [{"role": "user", "content": "hi"}]


def test_system_message_moves_to_instructions():
    payload = {
        "model": "gpt-5.1",
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
        ],
    }
    request = ResponsesRequest.model_validate(payload)

    assert request.instructions == "sys"
    assert request.input == [{"role": "user", "content": "hi"}]


def test_store_defaults_false():
    payload = {"model": "gpt-5.1"}
    request = ResponsesRequest.model_validate(payload)

    assert request.store is False
    assert "store" not in request.to_payload()


def test_store_true_is_rejected():
    payload = {"model": "gpt-5.1", "store": True}
    with pytest.raises(ValueError, match="store must be false"):
        ResponsesRequest.model_validate(payload)


def test_store_false_is_preserved():
    payload = {"model": "gpt-5.1", "store": False}
    request = ResponsesRequest.model_validate(payload)

    assert request.to_payload()["store"] is False


def test_max_output_tokens_removed_from_payload():
    payload = {"model": "gpt-5.1", "max_output_tokens": 32000}
    request = ResponsesRequest.model_validate(payload)

    dumped = request.to_payload()
    assert "max_output_tokens" not in dumped
