"""Загрузка и проверка конфигурации бота."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - запасной путь для минимальной среды

    def load_dotenv(*args: object, **kwargs: object) -> bool:
        return False


DEFAULT_MAX_CONTEXT_MESSAGES = 10
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_OUTPUT_TOKENS = 1000
DEFAULT_STATE_FILE = Path(".bot_state.json")
DEFAULT_PROMPTS_FILE = Path("prompts.json")
ALLOWED_ID_SPLIT_RE = re.compile(r"[,\s;]+")


@dataclass(slots=True)
class AppConfig:
    """Настройки приложения, собранные из окружения."""

    telegram_bot_token: str
    yandex_cloud_folder: str
    yandex_cloud_api_key: str
    yandex_cloud_model: str
    yandex_cloud_model_art: str
    allowed_user_ids: tuple[int, ...]
    max_context_messages: int
    temperature: float
    max_output_tokens: int
    state_file: Path
    prompts_file: Path


def load_settings(
    env: Mapping[str, str] | None = None,
    dotenv_path: str | Path | None = None,
) -> AppConfig:
    """Собирает настройки из `.env` или переданного отображения."""

    if env is None:
        load_dotenv(dotenv_path=dotenv_path or ".env")
        env = os.environ

    telegram_bot_token = _required(env, "TELEGRAM_BOT_TOKEN")
    yandex_cloud_folder = _required(env, "YANDEX_CLOUD_FOLDER")
    yandex_cloud_api_key = _required(env, "YANDEX_CLOUD_API_KEY")
    yandex_cloud_model = _required(env, "YANDEX_CLOUD_MODEL")
    yandex_cloud_model_art = _required(env, "YANDEX_CLOUD_MODEL_ART")
    allowed_user_ids = _parse_allowed_ids(_required(env, "ALLOWED_USER_IDS"))

    return AppConfig(
        telegram_bot_token=telegram_bot_token,
        yandex_cloud_folder=yandex_cloud_folder,
        yandex_cloud_api_key=yandex_cloud_api_key,
        yandex_cloud_model=yandex_cloud_model,
        yandex_cloud_model_art=yandex_cloud_model_art,
        allowed_user_ids=allowed_user_ids,
        max_context_messages=_parse_positive_int(
            env.get("MAX_CONTEXT_MESSAGES", str(DEFAULT_MAX_CONTEXT_MESSAGES)),
            "MAX_CONTEXT_MESSAGES",
        ),
        temperature=_parse_float(
            env.get("TEMPERATURE", str(DEFAULT_TEMPERATURE)), "TEMPERATURE"
        ),
        max_output_tokens=_parse_positive_int(
            env.get("MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS)),
            "MAX_OUTPUT_TOKENS",
        ),
        state_file=Path(env.get("STATE_FILE", str(DEFAULT_STATE_FILE))).expanduser(),
        prompts_file=Path(
            env.get("PROMPTS_FILE", str(DEFAULT_PROMPTS_FILE))
        ).expanduser(),
    )


def _required(env: Mapping[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise ValueError(f"Не задана обязательная переменная окружения: {key}")
    return value


def _parse_positive_int(raw_value: str, key: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Переменная {key} должна быть целым числом") from exc
    if value <= 0:
        raise ValueError(f"Переменная {key} должна быть больше нуля")
    return value


def _parse_float(raw_value: str, key: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Переменная {key} должна быть числом") from exc
    if value < 0:
        raise ValueError(f"Переменная {key} не может быть отрицательной")
    return value


def _parse_allowed_ids(raw_value: str) -> tuple[int, ...]:
    parts = [item for item in ALLOWED_ID_SPLIT_RE.split(raw_value.strip()) if item]
    if not parts:
        raise ValueError("ALLOWED_USER_IDS должен содержать хотя бы один id")

    allowed_ids: list[int] = []
    for part in parts:
        try:
            allowed_id = int(part)
        except ValueError as exc:
            raise ValueError(
                "ALLOWED_USER_IDS должен содержать только целые id пользователей"
            ) from exc
        allowed_ids.append(allowed_id)
    return tuple(allowed_ids)
