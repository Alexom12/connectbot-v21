# bots/bot_instance.py
import logging
from telegram.ext import Application
from config.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

_application_instance = None

def get_bot_instance() -> Application:
    """Возвращает синглтон-экземпляр Application."""
    global _application_instance
    if _application_instance is None:
        _application_instance = create_bot_application()
    return _application_instance

def set_bot_instance(application: Application):
    """Устанавливает глобальный экземпляр Application."""
    global _application_instance
    _application_instance = application

def create_bot_application():
    """Создание и настройка приложения бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден!")
        raise ValueError("Не установлен токен для Telegram бота.")
        
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("✅ Экземпляр бота успешно создан")
        return application
    except Exception as e:
        logger.error(f"❌ Ошибка создания экземпляра бота: {e}")
        raise e

# Этот файл больше не должен содержать логику настройки обработчиков.
# Логика перенесена в runbot_fixed_main.py
