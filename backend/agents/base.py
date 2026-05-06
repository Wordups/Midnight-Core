from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class AgentValidationError(ValueError):
    """Raised when an agent receives invalid input or produces invalid output."""


class BaseAgent(ABC):
    name: str = "base_agent"
    role: str = "Base Agent"
    allowed_actions: Sequence[str] = ()
    forbidden_actions: Sequence[str] = ()

    def validate_input(self, data: Any) -> Any:
        return data

    def validate_output(self, data: Any) -> Any:
        return data

    def run(self, data: Any) -> Any:
        validated_input = self.validate_input(data)
        result = self._run(validated_input)
        return self.validate_output(result)

    @abstractmethod
    def _run(self, data: Any) -> Any:
        raise NotImplementedError
