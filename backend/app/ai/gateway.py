from __future__ import annotations

import json
import logging
import time

from typing import Any, TypeVar

from pydantic import (
    BaseModel,
    ValidationError,
)

from app.ai.providers.gemini import (
    GeminiProvider,
)

from app.ai.providers.groq import (
    GroqProvider,
)

from app.core.config import settings

from app.models.ai_request import (
    AIRequest,
)


T = TypeVar(
    "T",
    bound=BaseModel,
)

logger = logging.getLogger(
    __name__
)


class AIGateway:
    def __init__(
        self,
        db,
        organization_id: str,
        provider=None,
    ):
        self.db = db

        self.organization_id = (
            organization_id
        )

        self.provider = provider

    # =====================================================
    # Providers
    # =====================================================

    def _providers(self):
        if self.provider is not None:
            return [self.provider]

        if settings.AI_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                raise RuntimeError(
                    "Gemini is selected but "
                    "GEMINI_API_KEY is not configured"
                )

            return [
                GeminiProvider()
            ]

        if settings.AI_PROVIDER == "groq":
            if not settings.GROQ_API_KEY:
                raise RuntimeError(
                    "Groq is selected but "
                    "GROQ_API_KEY is not configured"
                )

            return [
                GroqProvider()
            ]

        providers = []

        if settings.GEMINI_API_KEY:
            providers.append(
                GeminiProvider()
            )

        if settings.GROQ_API_KEY:
            providers.append(
                GroqProvider()
            )

        if not providers:
            raise RuntimeError(
                "AI is not configured. "
                "Add a free-tier "
                "GEMINI_API_KEY or GROQ_API_KEY "
                "in backend/.env"
            )

        if not (
            settings.AI_FALLBACK_TO_SECONDARY
        ):
            return providers[:1]

        return providers

    # =====================================================
    # Database audit
    # =====================================================

    def _record(
        self,
        *,
        provider: str,
        model: str,
        operation: str,
        prompt: str,
        output: str,
        started: float,
        success: bool,
    ) -> None:

        self.db.add(
            AIRequest(
                organization_id=(
                    self.organization_id
                ),

                provider=provider,

                model=model,

                operation=operation,

                input_text=(
                    prompt
                    if settings.AI_LOG_CONTENT
                    else "[redacted]"
                ),

                output_text=(
                    output
                    if settings.AI_LOG_CONTENT
                    else (
                        "[redacted]"
                        if success
                        else output[:500]
                    )
                ),

                latency_ms=(
                    time.perf_counter()
                    - started
                )
                * 1000,

                success=success,
            )
        )

        self.db.flush()

    # =====================================================
    # JSON schema cleanup
    # =====================================================

    @staticmethod
    def _clean_json_schema(
        value: Any,
    ) -> Any:

        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}

            for key, item in value.items():
                if key in {
                    "title",
                    "default",
                    "examples",
                    "$schema",
                }:
                    continue

                cleaned[key] = (
                    AIGateway
                    ._clean_json_schema(
                        item
                    )
                )

            return cleaned

        if isinstance(value, list):
            return [
                AIGateway
                ._clean_json_schema(item)

                for item in value
            ]

        return value

    # =====================================================
    # Errors
    # =====================================================

    @staticmethod
    def _describe_error(
        exc: Exception | None,
    ) -> str:

        if exc is None:
            return (
                "unknown AI provider error"
            )

        if isinstance(
            exc,
            ValidationError,
        ):
            problems = []

            for item in exc.errors()[:5]:
                location = ".".join(
                    str(part)
                    for part
                    in item.get(
                        "loc",
                        [],
                    )
                )

                message = item.get(
                    "msg",
                    "validation error",
                )

                if location:
                    problems.append(
                        f"{location}: {message}"
                    )
                else:
                    problems.append(
                        message
                    )

            return (
                "structured output "
                "validation failed: "
                + "; ".join(problems)
            )

        if isinstance(
            exc,
            json.JSONDecodeError,
        ):
            return (
                "provider returned "
                "invalid JSON"
            )

        message = str(exc).strip()

        if message:
            return (
                f"{type(exc).__name__}: "
                f"{message[:700]}"
            )

        return type(exc).__name__

    def _record_failure(
        self,
        provider,
        operation: str,
        prompt: str,
        started: float,
        exc: Exception,
    ) -> None:

        message = self._describe_error(
            exc
        )

        self._record(
            provider=getattr(
                provider,
                "name",
                "unknown",
            ),

            model=getattr(
                provider,
                "model",
                "unknown",
            ),

            operation=operation,

            prompt=prompt,

            output=message,

            started=started,

            success=False,
        )

        logger.warning(
            "AI provider %s failed "
            "for %s: %s",

            getattr(
                provider,
                "name",
                "unknown",
            ),

            operation,

            message,
        )

    # =====================================================
    # Standard generation
    # =====================================================

    def generate(
        self,
        operation: str,
        prompt: str,
        json_mode: bool = False,
    ) -> dict[str, Any]:

        providers = self._providers()

        last_error: (
            Exception | None
        ) = None

        for index, provider in enumerate(
            providers
        ):
            started = (
                time.perf_counter()
            )

            try:
                raw = provider.generate(
                    prompt,

                    json_mode=json_mode,

                    operation=operation,
                )

                output = (
                    json.loads(raw)
                    if json_mode
                    else raw
                )

                self._record(
                    provider=provider.name,

                    model=provider.model,

                    operation=operation,

                    prompt=prompt,

                    output=raw,

                    started=started,

                    success=True,
                )

                return {
                    "provider": (
                        provider.name
                    ),

                    "model": (
                        provider.model
                    ),

                    "output": output,

                    "fallback": (
                        index > 0
                    ),
                }

            except Exception as exc:
                last_error = exc

                self._record_failure(
                    provider,
                    operation,
                    prompt,
                    started,
                    exc,
                )

        raise RuntimeError(
            "All configured AI providers "
            "failed. Last error: "
            + self._describe_error(
                last_error
            )
        ) from last_error

    # =====================================================
    # Structured generation
    # =====================================================

    def generate_structured(
        self,
        operation: str,
        prompt: str,
        schema: type[T],
    ) -> dict[str, Any]:

        providers = self._providers()

        last_error: (
            Exception | None
        ) = None

        provider_schema = (
            self._clean_json_schema(
                schema.model_json_schema()
            )
        )

        schema_text = json.dumps(
            provider_schema,

            ensure_ascii=False,
        )

        structured_prompt = (
            f"{prompt}\n\n"

            "STRUCTURED OUTPUT REQUIREMENT:\n"

            "Return exactly one JSON object "
            "matching this JSON Schema. "

            "Do not add markdown or commentary "
            "outside the JSON object.\n"

            f"{schema_text}"
        )

        for index, provider in enumerate(
            providers
        ):
            current_prompt = (
                structured_prompt
            )

            # One correction attempt if the
            # model returns malformed output.
            for attempt in range(2):

                started = (
                    time.perf_counter()
                )

                try:
                    raw = provider.generate(
                        current_prompt,

                        json_mode=True,

                        operation=operation,

                        response_schema=(
                            provider_schema
                        ),
                    )

                    parsed = json.loads(
                        raw
                    )

                    validated = (
                        schema.model_validate(
                            parsed
                        )
                    )

                    normalized = (
                        validated.model_dump(
                            mode="json"
                        )
                    )

                    self._record(
                        provider=(
                            provider.name
                        ),

                        model=(
                            provider.model
                        ),

                        operation=operation,

                        prompt=(
                            current_prompt
                        ),

                        output=json.dumps(
                            normalized,

                            ensure_ascii=False,
                        ),

                        started=started,

                        success=True,
                    )

                    return {
                        "provider": (
                            provider.name
                        ),

                        "model": (
                            provider.model
                        ),

                        "output": (
                            normalized
                        ),

                        "fallback": (
                            index > 0
                        ),
                    }

                except (
                    ValidationError,
                    json.JSONDecodeError,
                    ValueError,
                ) as exc:

                    last_error = exc

                    self._record_failure(
                        provider,
                        operation,
                        current_prompt,
                        started,
                        exc,
                    )

                    if attempt == 0:
                        current_prompt = (
                            f"{structured_prompt}"
                            "\n\n"
                            "Your previous response "
                            "did not pass validation. "
                            "Return a corrected JSON "
                            "object only."
                        )

                        continue

                    break

                except Exception as exc:
                    last_error = exc

                    self._record_failure(
                        provider,
                        operation,
                        current_prompt,
                        started,
                        exc,
                    )

                    # Provider/model/network errors
                    # should move to secondary
                    # provider instead of doing a
                    # schema repair retry.
                    break

        raise RuntimeError(
            "All configured AI providers "
            "failed. Last error: "
            + self._describe_error(
                last_error
            )
        ) from last_error