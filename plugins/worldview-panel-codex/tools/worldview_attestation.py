#!/usr/bin/env python3

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from worldview_contracts import canonical_json_bytes, sha256_prefixed


TURN_RENDERER_VERSION = "turn_renderer_v1"
DEFAULT_NEWLINE_POLICY = "lf"
DEFAULT_ENCODING = "utf-8"


def _collect_user_message_texts(value: Any) -> list[str]:
    texts: list[str] = []

    if isinstance(value, Mapping):
        if value.get("type") == "userMessage" and isinstance(value.get("text"), str):
            texts.append(value["text"])
        for child in value.values():
            texts.extend(_collect_user_message_texts(child))
        return texts

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            texts.extend(_collect_user_message_texts(child))

    return texts


def _build_user_message_details(
    *,
    turn_input: Any,
    observed_user_text_fingerprint: str,
    observed_user_text: str,
    encoding: str,
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    user_texts = _collect_user_message_texts(turn_input)

    for index, text in enumerate(user_texts):
        fingerprint = sha256_prefixed(text.encode(encoding))
        detail: dict[str, Any] = {
            "index": index,
            "source": "turn_input",
            "text": text,
            "fingerprint": fingerprint,
            "byte_length": len(text.encode(encoding)),
        }
        if fingerprint == observed_user_text_fingerprint:
            detail["observed"] = True
        details.append(detail)

    if not any(detail["fingerprint"] == observed_user_text_fingerprint for detail in details):
        details.append(
            {
                "index": len(details),
                "source": "observed_user_text",
                "text": observed_user_text,
                "fingerprint": observed_user_text_fingerprint,
                "byte_length": len(observed_user_text.encode(encoding)),
                "observed": True,
            }
        )

    return details


def build_attestation(
    *,
    packet_fingerprint: str,
    turn_input: dict[str, Any],
    observed_user_text: str,
    renderer_version: str = TURN_RENDERER_VERSION,
    newline_policy: str = DEFAULT_NEWLINE_POLICY,
    encoding: str = DEFAULT_ENCODING,
) -> dict[str, Any]:
    turn_input_fingerprint = sha256_prefixed(canonical_json_bytes(turn_input))
    observed_user_text_fingerprint = sha256_prefixed(observed_user_text.encode(encoding))

    return {
        "schema_version": "attestation_v1",
        "packet_fingerprint": packet_fingerprint,
        "turn_input_fingerprint": turn_input_fingerprint,
        "turn_user_text_fingerprint": observed_user_text_fingerprint,
        "turn_input_user_messages": _build_user_message_details(
            turn_input=turn_input,
            observed_user_text_fingerprint=observed_user_text_fingerprint,
            observed_user_text=observed_user_text,
            encoding=encoding,
        ),
        "renderer_version": renderer_version,
        "newline_policy": newline_policy,
        "encoding": encoding,
    }
