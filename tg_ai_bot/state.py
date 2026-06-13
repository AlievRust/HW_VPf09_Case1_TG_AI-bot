"""Локальное JSON-хранилище для ролей и истории диалогов."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ChatMessage:
    """Одно сообщение в локальной истории."""

    role: str
    content: str


@dataclass(slots=True)
class UserSession:
    """Состояние одного пользователя."""

    role: str
    messages: list[ChatMessage] = field(default_factory=list)


class JsonStateStore:
    """Хранит состояние пользователей в одном JSON-файле."""

    def __init__(self, path: str | Path, max_context_messages: int) -> None:
        if max_context_messages <= 0:
            raise ValueError("max_context_messages должен быть больше нуля")
        self.path = Path(path)
        self.max_context_messages = max_context_messages
        self._lock = threading.Lock()
        self._state: dict[str, UserSession] = self._load()

    def get_role(self, user_id: int, default_role: str) -> str:
        """Возвращает активную роль пользователя, создавая сессию при необходимости."""

        with self._lock:
            session = self._state.get(str(user_id))
            if session is None:
                session = UserSession(role=default_role)
                self._state[str(user_id)] = session
                self._save_unlocked()
            return session.role

    def get_messages(self, user_id: int) -> list[ChatMessage]:
        """Возвращает копию истории пользователя."""

        with self._lock:
            session = self._state.get(str(user_id))
            if session is None:
                return []
            return [ChatMessage(role=item.role, content=item.content) for item in session.messages]

    def set_role(self, user_id: int, role: str, default_role: str) -> None:
        """Меняет активную роль, не затрагивая историю."""

        with self._lock:
            session = self._state.get(str(user_id))
            if session is None:
                session = UserSession(role=default_role)
                self._state[str(user_id)] = session
            session.role = role
            self._save_unlocked()

    def reset_user(self, user_id: int, default_role: str) -> None:
        """Очищает историю и возвращает роль по умолчанию."""

        with self._lock:
            self._state[str(user_id)] = UserSession(role=default_role)
            self._save_unlocked()

    def append_message(self, user_id: int, role: str, content: str, default_role: str) -> None:
        """Добавляет сообщение и обрезает историю до лимита."""

        with self._lock:
            session = self._state.get(str(user_id))
            if session is None:
                session = UserSession(role=default_role)
                self._state[str(user_id)] = session
            session.messages.append(ChatMessage(role=role, content=content))
            if len(session.messages) > self.max_context_messages:
                session.messages = session.messages[-self.max_context_messages :]
            self._save_unlocked()

    def snapshot(self) -> dict[str, UserSession]:
        """Возвращает копию всего хранилища для тестов и отладки."""

        with self._lock:
            return {
                user_id: UserSession(
                    role=session.role,
                    messages=[
                        ChatMessage(role=item.role, content=item.content)
                        for item in session.messages
                    ],
                )
                for user_id, session in self._state.items()
            }

    def _load(self) -> dict[str, UserSession]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
        if not isinstance(raw_data, dict):
            raise ValueError("Файл состояния должен содержать JSON-объект")

        state: dict[str, UserSession] = {}
        for user_id, raw_session in raw_data.items():
            if not isinstance(raw_session, dict):
                raise ValueError(f"Состояние пользователя {user_id} должно быть объектом")
            role = raw_session.get("role")
            if not isinstance(role, str) or not role:
                raise ValueError(f"У пользователя {user_id} не задана роль")
            raw_messages = raw_session.get("messages", [])
            if not isinstance(raw_messages, list):
                raise ValueError(f"У пользователя {user_id} сообщения должны быть списком")
            messages: list[ChatMessage] = []
            for raw_message in raw_messages[-self.max_context_messages :]:
                if not isinstance(raw_message, dict):
                    raise ValueError(
                        f"Сообщения пользователя {user_id} должны быть объектами"
                    )
                message_role = raw_message.get("role")
                content = raw_message.get("content")
                if not isinstance(message_role, str) or not isinstance(content, str):
                    raise ValueError(
                        f"Сообщения пользователя {user_id} содержат некорректные поля"
                    )
                messages.append(ChatMessage(role=message_role, content=content))
            state[str(user_id)] = UserSession(role=role, messages=messages)
        return state

    def _save_unlocked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        data = {
            user_id: {
                "role": session.role,
                "messages": [
                    {"role": item.role, "content": item.content}
                    for item in session.messages
                ],
            }
            for user_id, session in self._state.items()
        }
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temp_path.replace(self.path)
