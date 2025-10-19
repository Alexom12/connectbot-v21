# bots/handlers/common_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение со списком доступных команд."""
    
    help_text = (
        "🤖 *Справочный центр Connect-Bot*\n\n"
        "Вот список доступных вам команд:\n\n"
        "*/start* - Перезапустить бота и проверить авторизацию.\n"
        "*/help* - Показать это справочное сообщение.\n\n"
        "☕️ *Тайный кофе*\n"
        "*/feedback* - Оставить отзыв о последней встрече.\n\n"
        "Если у вас возникли проблемы, обратитесь к администратору."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
