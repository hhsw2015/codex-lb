from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.types import JsonObject, JsonValue


class ResponsesReasoning(BaseModel):
    model_config = ConfigDict(extra="allow")

    effort: str | None = None
    summary: str | None = None


class ResponsesTextFormat(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True, serialize_by_alias=True)

    type: str | None = None
    strict: bool | None = None
    schema_: JsonValue | None = Field(default=None, alias="schema")
    name: str | None = None


class ResponsesTextControls(BaseModel):
    model_config = ConfigDict(extra="allow")

    verbosity: str | None = None
    format: ResponsesTextFormat | None = None


class ResponsesRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    instructions: str = ""
    input: list[JsonValue] = Field(default_factory=list)
    tools: list[JsonValue] = Field(default_factory=list)
    tool_choice: str | None = None
    parallel_tool_calls: bool | None = None
    reasoning: ResponsesReasoning | None = None
    store: bool = False
    stream: bool | None = None
    include: list[str] = Field(default_factory=list)
    prompt_cache_key: str | None = None
    text: ResponsesTextControls | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_messages(cls, data: object) -> object:
        return _coerce_messages_payload(data)

    @field_validator("store")
    @classmethod
    def _ensure_store_false(cls, value: bool) -> bool:
        if value is True:
            raise ValueError("store must be false")
        return value

    def to_payload(self) -> JsonObject:
        payload = self.model_dump(mode="json", exclude_none=True)
        if "store" not in self.model_fields_set:
            payload.pop("store", None)
        return _strip_unsupported_fields(payload)


class ResponsesCompactRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    instructions: str = ""
    input: list[JsonValue] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_messages(cls, data: object) -> object:
        return _coerce_messages_payload(data)

    def to_payload(self) -> JsonObject:
        payload = self.model_dump(mode="json", exclude_none=True)
        return _strip_unsupported_fields(payload)


def _merge_instructions(existing: str, extra_parts: list[str]) -> str:
    if not extra_parts:
        return existing
    extra = "\n".join([part for part in extra_parts if part])
    if not extra:
        return existing
    if existing:
        return f"{existing}\n{extra}"
    return extra


def _content_to_text(content: object) -> str | None:
    if content is None:
        return None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                part_dict = cast(dict[str, JsonValue], part)
                text = part_dict.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join([part for part in parts if part])
    if isinstance(content, dict):
        content_dict = cast(dict[str, JsonValue], content)
        text = content_dict.get("text")
        if isinstance(text, str):
            return text
        return None
    return None


def _coerce_messages_payload(data: object) -> object:
    if not isinstance(data, dict):
        return data
    data_dict = cast(dict[str, JsonValue], data)
    if "messages" not in data_dict:
        return data_dict
    input_value = data_dict.get("input")
    if input_value not in (None, []):
        raise ValueError("Provide either 'input' or 'messages', not both.")
    messages = data_dict.get("messages")
    if not isinstance(messages, list):
        raise ValueError("'messages' must be a list.")

    instructions_parts: list[str] = []
    input_messages: list[JsonValue] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Each message must be an object.")
        message_dict = cast(dict[str, JsonValue], message)
        role_value = message_dict.get("role")
        role = role_value if isinstance(role_value, str) else None
        if role in ("system", "developer"):
            content_text = _content_to_text(message_dict.get("content"))
            if content_text:
                instructions_parts.append(content_text)
            continue
        input_messages.append(cast(JsonValue, message_dict))

    result: dict[str, JsonValue] = dict(data_dict)
    result.pop("messages", None)
    result["input"] = input_messages
    existing_instructions = result.get("instructions")
    if isinstance(existing_instructions, str) and existing_instructions:
        result["instructions"] = _merge_instructions(existing_instructions, instructions_parts)
    else:
        result["instructions"] = "\n".join([part for part in instructions_parts if part])
    return result


_UNSUPPORTED_UPSTREAM_FIELDS = {"max_output_tokens"}


def _strip_unsupported_fields(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    for key in _UNSUPPORTED_UPSTREAM_FIELDS:
        payload.pop(key, None)
    return payload
