# bots/shared_bot.py
import asyncio
from telegram import Bot
from config.settings import TELEGRAM_TOKEN
import logging

logger = logging.getLogger(__name__)

class BotManager:
    """
    Управляет единственным экземпляром бота, чтобы избежать частых переподключений.
    """
    _bot_instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_bot(cls) -> Bot:
        """
        Возвращает синглтон-экземпляр бота.
        """
        if cls._bot_instance is None:
            async with cls._lock:
                # Двойная проверка на случай, если несколько корутин ждали lock
                if cls._bot_instance is None:
                    if not TELEGRAM_TOKEN:
                        raise ValueError("Токен Telegram не найден.")
                    logger.info("Создание нового экземпляра Bot...")
                    cls._bot_instance = Bot(token=TELEGRAM_TOKEN)
        return cls._bot_instance

    @classmethod
    async def close_bot(cls):
        """
        Закрывает соединение бота, если оно было создано.
        """
        if cls._bot_instance:
            async with cls._lock:
                if cls._bot_instance:
                    logger.info("Закрытие экземпляра Bot...")
                    await cls._bot_instance.close()
                    cls._bot_instance = None

# Создаем экземпляр менеджера для импорта в других модулях
bot_manager = BotManager()
