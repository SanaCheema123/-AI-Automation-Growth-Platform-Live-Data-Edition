from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.ai.providers.base import AIProvider
from app.core.config import settings


class GroqProvider(AIProvider):
    name = "groq"

    API_URL = (
        "https://api.groq.com/openai/v1"
        "/chat/completions"
    )

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        client: httpx.Client | None = None,
    ):
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        if not settings.GROQ_MODEL:
            raise RuntimeError(
                "GROQ_MODEL is not configured"
            )

        self.client = client or httpx.Client(
            timeout=settings.GROQ_TIMEOUT_SECONDS
        )

        self.model = settings.GROQ_MODEL

    @staticmethod
    def _error_message(
        response: httpx.Response,
    ) -> str:
        try:
            payload = response.json()

            error = payload.get("error") or {}

            message = error.get("message")

            if message:
                return str(message)

        except Exception:
            pass

        text = (response.text or "").strip()

        if text:
            return text[:800]

        return "Unknown Groq API error"

    @staticmethod
    def _schema_name(
        operation: str,
    ) -> str:
        cleaned = re.sub(
            r"[^a-zA-Z0-9_]+",
            "_",
            operation,
        ).strip("_")

        return (
            cleaned
            or "structured_response"
        )[:64]

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        operation: str = "generation",
        response_schema: dict[str, Any] | None = None,
    ) -> str:

        body: dict[str, Any] = {
            "model": self.model,

            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            "temperature": 0.2,
        }

        if json_mode and response_schema:
            body["response_format"] = {
                "type": "json_schema",

                "json_schema": {
                    "name": (
                        self._schema_name(
                            operation
                        )
                    ),

                    "strict": True,

                    "schema": (
                        response_schema
                    ),
                },
            }

        elif json_mode:
            body["response_format"] = {
                "type": "json_object"
            }

        headers = {
            "Authorization": (
                f"Bearer "
                f"{settings.GROQ_API_KEY}"
            ),

            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(
            settings.GROQ_MAX_RETRIES + 1
        ):
            try:
                response = self.client.post(
                    self.API_URL,
                    headers=headers,
                    json=body,
                )

                if response.status_code >= 400:
                    message = (
                        self._error_message(
                            response
                        )
                    )

                    if (
                        response.status_code
                        in self.RETRYABLE_STATUS_CODES
                        and attempt
                        < settings.GROQ_MAX_RETRIES
                    ):
                        time.sleep(
                            0.5 * (2**attempt)
                        )
                        continue

                    raise RuntimeError(
                        "Groq API returned "
                        f"HTTP {response.status_code}: "
                        f"{message}"
                    )

                payload = response.json()

                choices = (
                    payload.get("choices")
                    or []
                )

                if not choices:
                    raise RuntimeError(
                        "Groq returned no choices"
                    )

                message = (
                    choices[0].get("message")
                    or {}
                )

                text = str(
                    message.get("content")
                    or ""
                ).strip()

                if not text:
                    raise RuntimeError(
                        "Groq returned an "
                        "empty response"
                    )

                return text

            except RuntimeError:
                raise

            except (
                httpx.TimeoutException,
                httpx.TransportError,
            ) as exc:
                last_error = exc

                if (
                    attempt
                    < settings.GROQ_MAX_RETRIES
                ):
                    time.sleep(
                        0.5 * (2**attempt)
                    )
                    continue

                break

            except (
                ValueError,
                TypeError,
            ) as exc:
                raise RuntimeError(
                    "Groq returned an invalid "
                    "API response: "
                    f"{type(exc).__name__}"
                ) from exc

            except Exception as exc:
                last_error = exc

                if (
                    attempt
                    < settings.GROQ_MAX_RETRIES
                ):
                    time.sleep(
                        0.5 * (2**attempt)
                    )
                    continue

                break

        raise RuntimeError(
            "Groq request failed after retries: "
            f"{type(last_error).__name__}: "
            f"{str(last_error)[:300]}"
        ) from last_error