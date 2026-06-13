"""Telegram-обработчики для AI-бота."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from .config import AppConfig
from .llm import AliceAIClient
from .prompts import PromptCatalog, format_prompt_list
from .state import JsonStateStore


@dataclass(slots=True)
class BotServices:
    """Все зависимости бота в одном объекте."""

    config: AppConfig
    prompts: PromptCatalog
    state_store: JsonStateStore
    llm_client: AliceAIClient


def create_router(services: BotServices) -> Router:
    """Создает router с обработчиками команд и обычного текста."""

    router = Router()

    @router.message(Command("start"))
    async def handle_start(message: Message) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        user_id = _user_id(message)
        role_key = services.state_store.get_role(user_id, services.prompts.default_prompt)
        if role_key not in services.prompts.prompts:
            role_key = services.prompts.default_prompt
            services.state_store.set_role(user_id, role_key, services.prompts.default_prompt)
        role = services.prompts.get(role_key)
        await message.answer(
            "\n".join(
                [
                    "Привет! Я бот с Alice AI.",
                    f"Текущая роль: {role.name} ({role_key})",
                    "Доступные команды: /roles, /role <ключ>, /reset, /img <промпт>.",
                ]
            )
        )

    @router.message(Command("roles"))
    async def handle_roles(message: Message) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        await message.answer(format_prompt_list(services.prompts))

    @router.message(Command("role"))
    async def handle_role(message: Message, command: CommandObject) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        user_id = _user_id(message)
        role_key = (command.args or "").strip()
        if not role_key:
            await message.answer(
                "Укажите ключ роли: /role assistant. Используйте /roles, чтобы увидеть список."
            )
            return
        if role_key not in services.prompts.prompts:
            await message.answer(
                "Неизвестная роль. Используйте /roles, чтобы увидеть доступные варианты."
            )
            return
        services.state_store.set_role(user_id, role_key, services.prompts.default_prompt)
        role = services.prompts.get(role_key)
        await message.answer(f"Роль переключена на: {role.name} ({role_key})")

    @router.message(Command("reset"))
    async def handle_reset(message: Message) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        user_id = _user_id(message)
        services.state_store.reset_user(user_id, services.prompts.default_prompt)
        default_role = services.prompts.get(services.prompts.default_prompt)
        await message.answer(
            f"Контекст очищен. Роль возвращена к: {default_role.name} ({services.prompts.default_prompt})"
        )

    @router.message(Command("img"))
    async def handle_image(message: Message, command: CommandObject) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        prompt = (command.args or "").strip()
        if not prompt:
            await message.answer("Укажите промпт: /img нарисуй кота в космосе")
            return
        try:
            image_bytes = services.llm_client.generate_image(prompt)
        except Exception as exc:
            await message.answer(f"Не удалось сгенерировать изображение: {exc}")
            return
        photo = BufferedInputFile(image_bytes, filename="alice-image.png")
        await message.answer_photo(photo, caption=prompt)

    @router.message(lambda message: bool(message.text) and not message.text.startswith("/"))
    async def handle_text(message: Message) -> None:
        if not _is_allowed(message, services.config.allowed_user_ids):
            return
        text = (message.text or "").strip()
        if not text or text.startswith("/"):
            return
        user_id = _user_id(message)
        role_key = services.state_store.get_role(user_id, services.prompts.default_prompt)
        if role_key not in services.prompts.prompts:
            role_key = services.prompts.default_prompt
            services.state_store.set_role(user_id, role_key, services.prompts.default_prompt)
        role = services.prompts.get(role_key)
        history = services.state_store.get_messages(user_id)
        services.state_store.append_message(
            user_id,
            "user",
            text,
            services.prompts.default_prompt,
        )
        try:
            reply = services.llm_client.generate_reply(role.system_prompt, history, text)
        except Exception as exc:
            await message.answer(f"Не удалось получить ответ от модели: {exc}")
            return
        services.state_store.append_message(
            user_id,
            "assistant",
            reply,
            services.prompts.default_prompt,
        )
        await message.answer(reply)

    return router


def _is_allowed(message: Message, allowed_user_ids: tuple[int, ...]) -> bool:
    user = message.from_user
    if user is None:
        return False
    if user.id not in allowed_user_ids:
        return False
    return True


def _user_id(message: Message) -> int:
    user = message.from_user
    if user is None:
        raise ValueError("Сообщение не содержит данных пользователя")
    return user.id
