"""Позволяет запускать пакет командой `python -m tg_ai_bot`."""

from .main import main

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
