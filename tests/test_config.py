from __future__ import annotations

from pathlib import Path

import pytest

from tg_ai_bot.config import AppConfig, load_settings


def test_load_settings_parses_values() -> None:
    settings = load_settings(
        {
            "TELEGRAM_BOT_TOKEN": "token",
            "YANDEX_CLOUD_FOLDER": "folder",
            "YANDEX_CLOUD_API_KEY": "key",
            "YANDEX_CLOUD_MODEL": "aliceai-llm/latest",
            "YANDEX_CLOUD_MODEL_ART": "aliceai-image-art-3.0/latest",
            "ALLOWED_USER_IDS": "1, 2;3",
            "MAX_CONTEXT_MESSAGES": "12",
            "TEMPERATURE": "0.3",
            "MAX_OUTPUT_TOKENS": "256",
            "STATE_FILE": "state.json",
            "PROMPTS_FILE": "prompts.json",
        }
    )

    assert isinstance(settings, AppConfig)
    assert settings.telegram_bot_token == "token"
    assert settings.allowed_user_ids == (1, 2, 3)
    assert settings.max_context_messages == 12
    assert settings.temperature == 0.3
    assert settings.max_output_tokens == 256
    assert settings.state_file == Path("state.json")
    assert settings.prompts_file == Path("prompts.json")


def test_load_settings_requires_allowlist() -> None:
    with pytest.raises(ValueError, match="ALLOWED_USER_IDS"):
        load_settings(
            {
                "TELEGRAM_BOT_TOKEN": "token",
                "YANDEX_CLOUD_FOLDER": "folder",
                "YANDEX_CLOUD_API_KEY": "key",
                "YANDEX_CLOUD_MODEL": "aliceai-llm/latest",
                "YANDEX_CLOUD_MODEL_ART": "aliceai-image-art-3.0/latest",
            }
        )
