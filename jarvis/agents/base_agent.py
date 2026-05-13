from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.enabled = True
        self._confidence_threshold = 0.3

    @abstractmethod
    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        pass

    @abstractmethod
    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        pass

    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        self._confidence_threshold = max(0.0, min(1.0, value))

    def __repr__(self):
        return f"<Agent {self.name} enabled={self.enabled}>"
