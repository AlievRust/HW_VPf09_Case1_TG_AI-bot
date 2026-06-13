from __future__ import annotations

import json

import pytest

from tg_ai_bot.prompts import format_prompt_list, load_prompt_catalog


def test_load_prompt_catalog(tmp_path) -> None:
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps(
            {
                "default_prompt": "assistant",
                "prompts": {
                    "assistant": {
                        "name": "Помощник",
                        "description": "Обычный режим",
                        "system_prompt": "Ты полезный помощник.",
                    },
                    "teacher": {
                        "name": "Учитель",
                        "description": "Объясняет сложное",
                        "system_prompt": "Ты терпеливый преподаватель.",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    catalog = load_prompt_catalog(path)

    assert catalog.default_prompt == "assistant"
    assert catalog.get("teacher").name == "Учитель"
    rendered = format_prompt_list(catalog)
    assert "assistant" in rendered
    assert "Учитель" in rendered


def test_load_prompt_catalog_rejects_unknown_default(tmp_path) -> None:
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps(
            {
                "default_prompt": "missing",
                "prompts": {
                    "assistant": {
                        "name": "Помощник",
                        "description": "Обычный режим",
                        "system_prompt": "Ты полезный помощник.",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="default_prompt"):
        load_prompt_catalog(path)
