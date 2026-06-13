"""Точка входа Telegram-бота."""

from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher

from .bot import BotServices, create_router
from .config import load_settings
from .llm import AliceAIClient
from .prompts import load_prompt_catalog
from .state import JsonStateStore


async def main() -> None:
    """Запускает polling Telegram-бота."""

    try:
        config = load_settings()
        prompts = load_prompt_catalog(config.prompts_file)
        state_store = JsonStateStore(config.state_file, config.max_context_messages)
        llm_client = AliceAIClient(
            folder=config.yandex_cloud_folder,
            api_key=config.yandex_cloud_api_key,
            text_model=config.yandex_cloud_model,
            art_model=config.yandex_cloud_model_art,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
        )
    except Exception as exc:
        print(f"Ошибка запуска: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    services = BotServices(
        config=config,
        prompts=prompts,
        state_store=state_store,
        llm_client=llm_client,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router(services))

    bot = Bot(token=config.telegram_bot_token)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
