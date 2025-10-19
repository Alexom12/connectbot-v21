# bots/handlers/error_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

async def handle_unexpected_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает сообщения, которые не соответствуют ожидаемому состоянию диалога.
    """
    user_text = update.message.text
    logger.warning(f"Пользователь {update.effective_user.id} ввел '{user_text}' в неожиданном состоянии.")
    
    await update.message.reply_text(
        "🤔 Хм, я не ожидал этого сейчас. Кажется, мы сбились с пути.\n\n"
        "Давайте вернемся в главное меню. Используйте /start, чтобы продолжить."
    )
    
    return ConversationHandler.END

async def handle_text_instead_of_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает текстовые сообщения, когда ожидается нажатие на кнопку.
    """
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки для ответа, чтобы я мог вас понять. 😊"
    )

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок. Логирует ошибки и сообщает пользователю.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Попытка уведомить пользователя
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚙️ Ой, что-то пошло не так. Я уже сообщил об ошибке разработчикам. "
                "Пожалуйста, попробуйте еще раз через некоторое время."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")
