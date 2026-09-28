from __future__ import annotations

import time
from typing import Any

import httpx

from app.ai.providers.base import AIProvider
from app.core.config import settings


class GeminiProvider(AIProvider):
    name = "gemini"

    API_URL = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/interactions"
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
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        if not settings.GEMINI_MODEL:
            raise RuntimeError(
                "GEMINI_MODEL is not configured"
            )

        self.client = client or httpx.Client(
            timeout=settings.GEMINI_TIMEOUT_SECONDS
        )

        self.model = settings.GEMINI_MODEL

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

        return "Unknown Gemini API error"

    @staticmethod
    def _extract_text(
        payload: dict[str, Any],
    ) -> str:
        # Some representations may expose this directly.
        direct = payload.get("output_text")

        if (
            isinstance(direct, str)
            and direct.strip()
        ):
            return direct.strip()

        # Interactions REST response:
        #
        # steps:
        #   - type: model_output
        #     content:
        #       - type: text
        #         text: ...
        steps = payload.get("steps") or []

        for step in reversed(steps):
            if step.get("type") != "model_output":
                continue

            chunks: list[str] = []

            for item in step.get("content") or []:
                if (
                    item.get("type") == "text"
                    and item.get("text")
                ):
                    chunks.append(
                        str(item["text"])
                    )

            text = "".join(chunks).strip()

            if text:
                return text

        return ""

    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        operation: str = "generation",
        response_schema: dict[str, Any] | None = None,
    ) -> str:

        body: dict[str, Any] = {
            "model": self.model,
            "input": prompt,

            # We do not need Gemini to retain
            # these interactions server-side.
            "store": False,
        }

        if json_mode:
            response_format: dict[str, Any] = {
                "type": "text",
                "mime_type": "application/json",
            }

            if response_schema:
                response_format["schema"] = (
                    response_schema
                )

            body["response_format"] = (
                response_format
            )

        headers = {
            "x-goog-api-key": (
                settings.GEMINI_API_KEY
            ),
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(
            settings.GEMINI_MAX_RETRIES + 1
        ):
            try:
                response = self.client.post(
                    self.API_URL,
                    headers=headers,
                    json=body,
                )

                # -----------------------------------------
                # HTTP errors
                # -----------------------------------------

                if response.status_code >= 400:
                    message = (
                        self._error_message(response)
                    )

                    if (
                        response.status_code
                        in self.RETRYABLE_STATUS_CODES
                        and attempt
                        < settings.GEMINI_MAX_RETRIES
                    ):
                        time.sleep(
                            0.5 * (2**attempt)
                        )
                        continue

                    raise RuntimeError(
                        "Gemini API returned "
                        f"HTTP {response.status_code}: "
                        f"{message}"
                    )

                # -----------------------------------------
                # Parse response
                # -----------------------------------------

                payload = response.json()

                status = str(
                    payload.get("status")
                    or "completed"
                ).lower()

                if status in {
                    "failed",
                    "cancelled",
                }:
                    raise RuntimeError(
                        "Gemini interaction ended "
                        f"with status '{status}'"
                    )

                text = self._extract_text(
                    payload
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned no text output "
                        f"(interaction status: {status})"
                    )

                return text

            except RuntimeError:
                # Already contains safe useful error.
                raise

            except (
                httpx.TimeoutException,
                httpx.TransportError,
            ) as exc:
                last_error = exc

                if (
                    attempt
                    < settings.GEMINI_MAX_RETRIES
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
                    "Gemini returned an invalid "
                    "API response: "
                    f"{type(exc).__name__}"
                ) from exc

            except Exception as exc:
                last_error = exc

                if (
                    attempt
                    < settings.GEMINI_MAX_RETRIES
                ):
                    time.sleep(
                        0.5 * (2**attempt)
                    )
                    continue

                break

        raise RuntimeError(
            "Gemini request failed after retries: "
            f"{type(last_error).__name__}: "
            f"{str(last_error)[:300]}"
        ) from last_error