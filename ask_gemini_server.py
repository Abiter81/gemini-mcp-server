#!/usr/bin/env python3
"""Sicherer MCP-Server für Google Gemini (stdio transport).

API-Schlüssel werden ausschließlich aus GEMINI_API_KEY oder aus der Datei
GEMINI_API_KEY_FILE gelesen. Niemals Schlüssel in diesen Quelltext schreiben.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

from mcp.server.fastmcp import FastMCP

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 60.0
MAX_PROMPT_CHARS = 100_000

mcp = FastMCP("gemini-mcp")


def _api_key() -> str:
    """Liest den Schlüssel aus der Umgebung oder einer privaten Datei."""
    value = os.environ.get("GEMINI_API_KEY", "").strip()
    if value:
        return value
    key_file = os.environ.get("GEMINI_API_KEY_FILE", "").strip()
    if not key_file:
        raise RuntimeError(
            "Kein API-Schlüssel gefunden. Setze GEMINI_API_KEY oder "
            "GEMINI_API_KEY_FILE auf eine private Datei."
        )
    path = Path(key_file).expanduser()
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"API-Key-Datei kann nicht gelesen werden: {exc}") from exc
    if not value:
        raise RuntimeError("Die API-Key-Datei ist leer.")
    return value


def _request_gemini(prompt: str, model: str, temperature: float,
                    max_output_tokens: int, timeout: float) -> dict[str, Any]:
    key = _api_key()
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS endpoint
            raw = response.read()
    except HTTPError as exc:
        # Body is useful for diagnosis but may contain provider details; do not echo credentials.
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Gemini API nicht erreichbar: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Gemini API Timeout nach {timeout:g} Sekunden.") from exc
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini API lieferte keine gültige JSON-Antwort.") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Gemini API lieferte ein unerwartetes Antwortformat.")
    return result


def _text_from_response(result: dict[str, Any]) -> str:
    candidates = result.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        feedback = result.get("promptFeedback")
        if feedback:
            raise RuntimeError(f"Gemini hat die Anfrage abgelehnt: {feedback}")
        raise RuntimeError("Gemini lieferte keine Antwortkandidaten.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(
        part.get("text", "") for part in parts
        if isinstance(part, dict) and isinstance(part.get("text", ""), str)
    ).strip()
    if not text:
        reason = candidates[0].get("finishReason", "unbekannt")
        raise RuntimeError(f"Gemini lieferte keinen Text (finishReason: {reason}).")
    return text


@mcp.tool()
def ask_gemini(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
) -> str:
    """Beantwortet eine Textfrage mit Google Gemini.

    Der Dienst sendet den Prompt an die Google Gemini API. Verwende keine
    vertraulichen Daten, sofern deren Übermittlung nicht beabsichtigt ist.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt muss ein nichtleerer Text sein.")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"prompt darf höchstens {MAX_PROMPT_CHARS} Zeichen enthalten.")
    if not isinstance(model, str) or not model.strip() or "/" in model or ":" in model:
        raise ValueError("Ungültiger Modellname.")
    if not 0 <= temperature <= 2:
        raise ValueError("temperature muss zwischen 0 und 2 liegen.")
    if not 1 <= max_output_tokens <= 65_536:
        raise ValueError("max_output_tokens muss zwischen 1 und 65536 liegen.")
    result = _request_gemini(prompt.strip(), model.strip(), temperature,
                             max_output_tokens, DEFAULT_TIMEOUT)
    return _text_from_response(result)


if __name__ == "__main__":
    # FastMCP nutzt standardmäßig stdio; stdout bleibt für MCP-Nachrichten reserviert.
    mcp.run(transport="stdio")
