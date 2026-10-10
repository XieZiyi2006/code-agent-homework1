"""Bounded conversation memory used by the Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class ConversationMemory:
    """Keep the most recent messages so a long session stays bounded."""

    def __init__(self, max_messages: int = 12) -> None:
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2")
        self.max_messages = max_messages
        self._messages: List[Message] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append(Message(role=role, content=content))
        overflow = len(self._messages) - self.max_messages
        if overflow > 0:
            del self._messages[:overflow]

    def messages(self) -> List[Message]:
        return list(self._messages)

    def transcript(self, max_chars: int = 6000) -> str:
        lines = [f"{message.role}: {message.content}" for message in self._messages]
        text = "\n".join(lines)
        return text[-max_chars:]

    def clear(self) -> None:
        self._messages.clear()

