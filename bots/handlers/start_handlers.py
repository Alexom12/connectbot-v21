"""
Обработчики команд запуска и приветствия
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bots.menu_manager import MenuManager

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_message = f"""
👋 Привет, {user.first_name}!

🤖 Я ConnectBot v21 - твой помощник для корпоративных активностей!

📋 Мои возможности:
☕ Тайный кофе - найди коллегу для кофе-брейка
🎯 Активности - участвуй в корпоративных мероприятиях
📊 Статистика - отслеживай свою активность
⚙️ Настройки - управляй уведомлениями

Используй /menu для навигации по функциям.
    """
    
    await update.message.reply_text(welcome_message)
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🔧 СПРАВКА ПО CONNECTBOT

Основные команды:
/start - Запуск бота
/menu - Главное меню
/help - Эта справка
/profile - Твой профиль

☕ Тайный кофе:
/coffee - Участвовать в Тайном кофе
/coffee_status - Статус участия

🎯 Активности:
/activities - Доступные активности
/my_activities - Мои активности

⚙️ Настройки:
/settings - Настройки уведомлений
/interests - Управление интересами

📞 Поддержка: обратитесь к администратору
    """
    
    await update.message.reply_text(help_text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    # Отправляем интерактивное главное меню (кнопки)
    try:
        menu_manager = MenuManager()
        menu_data = await menu_manager.create_main_menu()
        await update.message.reply_text(**menu_data)
    except Exception as e:
        logger.error(f"Ошибка отправки интерактивного меню: {e}")
        # Фоллбэк на текстовое меню
        menu_text = """
📋 ГЛАВНОЕ МЕНЮ CONNECTBOT

Выберите действие:

☕ /coffee - Тайный кофе
🎯 /activities - Активности  
👤 /profile - Мой профиль
⚙️ /settings - Настройки
📊 /stats - Моя статистика
❓ /help - Справка

💡 Используйте команды или напишите сообщение для интерактивного меню
        """
        await update.message.reply_text(menu_text)

def setup_start_handlers(application: Application):
    """Настройка обработчиков команд запуска"""
    try:
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("menu", menu_command))
        
        logger.info("Обработчики команд запуска настроены")
        
    except Exception as e:
        logger.error(f"Ошибка настройки обработчиков запуска: {e}")