"""Клиент Alice AI для текста и изображений."""

from __future__ import annotations

import base64
import importlib
from dataclasses import dataclass
from typing import Sequence

from .state import ChatMessage


@dataclass(slots=True)
class AliceAIClient:
    """Минимальная обертка над OpenAI-совместимым клиентом Yandex Cloud."""

    folder: str
    api_key: str
    text_model: str
    art_model: str
    temperature: float
    max_output_tokens: int

    def generate_reply(
        self,
        system_prompt: str,
        history: Sequence[ChatMessage],
        user_text: str,
    ) -> str:
        """Генерирует текстовый ответ."""

        client = self._create_client()
        response = client.responses.create(
            model=self._text_model_uri,
            instructions=system_prompt,
            input=_build_transcript(history, user_text),
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )
        text = _extract_output_text(response)
        if not text:
            raise RuntimeError("Модель вернула пустой ответ")
        return text.strip()

    def generate_image(self, prompt: str) -> bytes:
        """Генерирует изображение и возвращает байты PNG."""

        client = self._create_client()
        response = client.images.generate(
            model=self._art_model_uri,
            prompt=prompt,
            size="1024x1024",
        )
        try:
            image_b64 = response.data[0].b64_json
        except (AttributeError, IndexError) as exc:
            raise RuntimeError("Модель не вернула изображение") from exc
        if not image_b64:
            raise RuntimeError("Модель не вернула изображение")
        return base64.b64decode(image_b64)

    @property
    def _text_model_uri(self) -> str:
        return f"gpt://{self.folder}/{self.text_model}"

    @property
    def _art_model_uri(self) -> str:
        return f"art://{self.folder}/{self.art_model}"

    def _create_client(self):
        try:
            openai_module = importlib.import_module("openai")
        except ImportError as exc:  # pragma: no cover - зависит от окружения
            raise RuntimeError(
                "Не установлен пакет openai. Установите зависимости из requirements.txt"
            ) from exc
        return openai_module.OpenAI(
            api_key=self.api_key,
            base_url="https://ai.api.cloud.yandex.net/v1",
            project=self.folder,
        )


def _build_transcript(history: Sequence[ChatMessage], user_text: str) -> str:
    lines = ["История диалога:"]
    if history:
        for message in history:
            speaker = "Пользователь" if message.role == "user" else "Ассистент"
            lines.append(f"{speaker}: {message.content}")
        lines.append("")
    lines.append(f"Пользователь: {user_text}")
    lines.append("Ассистент:")
    return "\n".join(lines)


def _extract_output_text(response: object) -> str:
    output_text = getattr(response, "output_text", "")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    output = getattr(response, "output", None)
    if not output:
        return ""
    collected: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not content:
            continue
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
            else:
                text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                collected.append(text)
    return "\n".join(collected)
