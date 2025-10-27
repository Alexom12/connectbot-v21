# bots/handlers/common_handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from bots.utils.message_utils import reply_with_menu
from bots.menu_manager import MenuManager

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение со списком доступных команд."""
    
    help_text = """
🤖 *Справочный центр Connect-Bot*

*Основные команды:*
/start - Перезапустить бота и проверить авторизацию
/help - Показать это справочное сообщение  
/menu - Главное меню с кнопками навигации

*Быстрая навигация через кнопки:*
👤 *Мой профиль* - информация и статистика
🎯 *Мои интересы* - управление подписками
📅 *Календарь* - ваши активности
🏅 *Достижения* - ваши награды
☕ *Тайный кофе* - анонимные встречи
⚙️ *Настройки* - настройки бота
❓ *Помощь* - справка и поддержка

☕️ *Тайный кофе*
/coffee - Участие в Тайном кофе
/feedback - Оставить отзыв о последней встрече

*Управление профилем:*
/profile - Мой профиль
/preferences - Настройка интересов
/stats - Моя статистика

💡 *Совет:* Используйте кнопки внизу экрана для быстрой навигации!

Если у вас возникли проблемы, обратитесь к администратору @hr_admin
"""
    
    await reply_with_menu(update, help_text, menu_type='help', parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отменяет текущую операцию и возвращает в главное меню."""
    
    cancel_text = """
❌ *Операция отменена*

Возвращаю вас в главное меню...
"""
    
    await reply_with_menu(update, cancel_text, menu_type='main', parse_mode='Markdown')

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает неизвестные команды."""
    
    unknown_text = """
🤔 *Неизвестная команда*

Я не понял, что вы имели в виду.

Попробуйте одну из этих команд:
/start - начать работу
/menu - открыть главное меню  
/help - получить справку

Или используйте кнопки ниже для навигации:
"""
    
    await reply_with_menu(update, unknown_text, menu_type='main', parse_mode='Markdown')

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения, которые не являются командами."""
    
    # Если сообщение не обработано другими обработчиками, показываем главное меню
    menu_text = await MenuManager.create_main_menu_message()
    await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')

def setup_common_handlers(application):
    """Настройка общих обработчиков"""
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Обработчик неизвестных сообщений (fallback)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_unknown_message
    ))