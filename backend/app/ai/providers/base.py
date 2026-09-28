from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    name = "provider"
    model = "unknown"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        json_mode: bool = False,
        operation: str = "generation",
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError