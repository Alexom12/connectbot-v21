# bots/handlers/feedback_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from activities.feedback_services import FeedbackService
from bots.services.user_service import format_user_for_logging
from bots.handlers.error_handlers import handle_text_instead_of_button, handle_unexpected_state

# Инициализация сервиса
feedback_service = FeedbackService()

# Настройка логирования
logger = logging.getLogger(__name__)

# Состояния диалога
ASK_RATING, ASK_COMMENT, ASK_SUGGESTIONS, ASK_FINAL = range(4)

async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс сбора обратной связи, показывая список встреч."""
    user = update.effective_user
    logger.info(f"Пользователь {format_user_for_logging(user)} инициировал сбор обратной связи.")

    pending_meetings = await feedback_service.get_pending_feedbacks_for_user(user.id)

    if not pending_meetings:
        await context.bot.send_message(chat_id=user.id, text="У вас нет встреч, ожидающих отзыва. Спасибо!")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                f"Встреча от {meeting.created_at.strftime('%d.%m')}",
                callback_data=f"feedback_{meeting.id}"
            )
        ]
        for meeting in pending_meetings
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=user.id,
        text="Пожалуйста, выберите встречу, для которой хотите оставить отзыв:",
        reply_markup=reply_markup
    )
    return ASK_RATING

async def ask_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает оценку для выбранной встречи."""
    query = update.callback_query
    await query.answer()
    meeting_id = int(query.data.split('_')[1])
    
    context.user_data[f'meeting_id_{meeting_id}'] = {'id': meeting_id}

    keyboard = [
        [InlineKeyboardButton(f"⭐{i}", callback_data=f"rating_{i}") for i in range(1, 6)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Оцените встречу от 1 до 5:", reply_markup=reply_markup)
    return ASK_COMMENT

async def handle_rating_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ввод текста на шаге оценки."""
    await handle_text_instead_of_button(update, context)

async def ask_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет оценку и запрашивает анонимный комментарий."""
    query = update.callback_query
    await query.answer()
    rating = int(query.data.split('_')[1])
    
    # Находим meeting_id в user_data
    meeting_key = next((key for key in context.user_data if key.startswith('meeting_id_')), None)
    if not meeting_key:
        await query.edit_message_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END
        
    context.user_data[meeting_key]['rating'] = rating
    
    await query.edit_message_text(text="Спасибо! Теперь напишите анонимный комментарий для партнера.")
    return ASK_SUGGESTIONS

async def ask_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет комментарий и запрашивает предложения."""
    comment = update.message.text
    
    meeting_key = next((key for key in context.user_data if key.startswith('meeting_id_')), None)
    if not meeting_key:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

    context.user_data[meeting_key]['comment'] = comment
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо! Теперь, если хотите, напишите предложения по улучшению. Если их нет, введите 'нет'.")
    return ASK_FINAL

async def end_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет предложения и завершает диалог."""
    suggestions = update.message.text
    user_id = update.effective_user.id

    meeting_key = next((key for key in context.user_data if key.startswith('meeting_id_')), None)
    if not meeting_key:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

    feedback_data = context.user_data[meeting_key]
    
    await feedback_service.submit_feedback(
        meeting_id=feedback_data['id'],
        user_telegram_id=user_id,
        rating=feedback_data['rating'],
        anonymous_feedback=feedback_data.get('comment', ''),
        suggestions=suggestions if suggestions.lower() not in ['нет', 'no'] else ''
    )
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Ваш отзыв принят! Спасибо за участие.")
    
    # Очистка
    if meeting_key in context.user_data:
        del context.user_data[meeting_key]
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Сбор отзыва отменен.")
    context.user_data.clear()
    return ConversationHandler.END

feedback_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("feedback", start_feedback)],
    states={
        ASK_RATING: [
            CallbackQueryHandler(ask_rating, pattern=r"^feedback_\d+$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_instead_of_button),
        ],
        ASK_COMMENT: [
            CallbackQueryHandler(ask_comment, pattern=r"^rating_[1-5]$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_instead_of_button),
        ],
        ASK_SUGGESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_suggestions)],
        ASK_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_feedback)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.ALL, handle_unexpected_state),
    ],
)
