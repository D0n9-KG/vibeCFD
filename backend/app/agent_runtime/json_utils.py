from __future__ import annotations

import json
from json import JSONDecodeError


def strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_json_object(raw: str) -> dict:
    text = strip_code_fence(raw)
    if not text:
        raise ValueError("Model response is empty; expected a JSON object.")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Could not extract a JSON object from the model response.")
