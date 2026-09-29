"""Запуск: python -m dietbot"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from .config import load_config
from .db import Database
from .handlers import router
from .runtime import check_anthropic_reachable, start_health_server
from .vision import FoodRecognizer


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    db = Database(cfg.db_path)
    await db.connect()
    await check_anthropic_reachable()
    health = await start_health_server()

    bot = Bot(cfg.bot_token)
    dp = Dispatcher(db=db, cfg=cfg, recognizer=FoodRecognizer(cfg.model))
    dp.include_router(router)
    await bot.set_my_commands([
        BotCommand(command="today", description="Итоги дня / Daily summary"),
        BotCommand(command="weight", description="Записать вес / Log weight"),
        BotCommand(command="start", description="Пересчитать план / Recalculate plan"),
        BotCommand(command="help", description="Помощь / Help"),
    ])
    try:
        await dp.start_polling(bot)
    finally:
        if health:
            await health.cleanup()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
