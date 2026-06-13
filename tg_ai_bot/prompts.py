"""Загрузка и форматирование ролей бота."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """Одна роль бота."""

    key: str
    name: str
    description: str
    system_prompt: str


@dataclass(frozen=True, slots=True)
class PromptCatalog:
    """Набор доступных ролей."""

    default_prompt: str
    prompts: dict[str, PromptDefinition]

    def get(self, key: str) -> PromptDefinition:
        try:
            return self.prompts[key]
        except KeyError as exc:
            raise KeyError(f"Неизвестная роль: {key}") from exc

    def iter_prompts(self) -> Iterable[PromptDefinition]:
        for key in sorted(self.prompts):
            yield self.prompts[key]


def load_prompt_catalog(path: str | Path) -> PromptCatalog:
    """Читает `prompts.json` и проверяет его структуру."""

    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Файл ролей не найден: {prompt_path}")

    with prompt_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    default_prompt = _required_string(raw_data, "default_prompt")
    raw_prompts = raw_data.get("prompts")
    if not isinstance(raw_prompts, dict) or not raw_prompts:
        raise ValueError("prompts.json должен содержать непустой словарь prompts")

    prompts: dict[str, PromptDefinition] = {}
    for key, value in raw_prompts.items():
        if not isinstance(value, dict):
            raise ValueError(f"Роль {key} должна быть объектом")
        prompts[key] = PromptDefinition(
            key=key,
            name=_required_string(value, "name"),
            description=_required_string(value, "description"),
            system_prompt=_required_string(value, "system_prompt"),
        )

    if default_prompt not in prompts:
        raise ValueError(
            "default_prompt должен ссылаться на существующую роль из prompts"
        )

    return PromptCatalog(default_prompt=default_prompt, prompts=prompts)


def format_prompt_list(catalog: PromptCatalog) -> str:
    """Собирает человекочитаемый список ролей."""

    lines = ["Доступные роли:"]
    for prompt in catalog.iter_prompts():
        marker = " (по умолчанию)" if prompt.key == catalog.default_prompt else ""
        lines.append(f"- {prompt.key}: {prompt.name}{marker}")
        lines.append(f"  {prompt.description}")
    return "\n".join(lines)


def _required_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Поле {key} должно быть непустой строкой")
    return value.strip()
