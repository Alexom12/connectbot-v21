import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config.settings import TELEGRAM_BOT_TOKEN
from bots.handlers import (
    start_handlers,
    menu_handlers, 
    secret_coffee_handlers,
    notification_handlers
)

logger = logging.getLogger(__name__)

def setup_handlers(application):
    """Настройка всех обработчиков бота"""
    
    # Базовые обработчики
    start_handlers.setup_start_handlers(application)
    menu_handlers.setup_menu_handlers(application)
    
    # Обработчики Тайного кофе
    secret_coffee_handlers.setup_secret_coffee_handlers(application)
    
    # Обработчики уведомлений
    notification_handlers.setup_notification_handlers(application)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в боте: {context.error}", exc_info=context.error)

def create_bot_application():
    """Создание и настройка приложения бота"""
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        setup_handlers(application)
        logger.info("✅ Бот успешно инициализирован")
        return application
    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        return None

# Глобальная переменная для доступа к приложению
application = create_bot_application()
from bots.handlers import preference_handlers

def setup_handlers(application):
    """Настройка всех обработчиков бота"""
    
    # Базовые обработчики
    start_handlers.setup_start_handlers(application)
    menu_handlers.setup_menu_handlers(application)
    
    # Обработчики предпочтений
    preference_handlers.setup_preference_handlers(application)
    
    # Обработчики Тайного кофе
    secret_coffee_handlers.setup_secret_coffee_handlers(application)
    
    # Обработчики уведомлений
    notification_handlers.setup_notification_handlers(application)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)