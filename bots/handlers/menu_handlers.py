from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bots.services.redis_service import redis_service
import logging

logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню с активностями"""
    user_id = update.effective_user.id
    
    # Получаем данные пользователя из кэша
    user_data = await redis_service.get_user_data(user_id)
    
    keyboard = [
        [InlineKeyboardButton("☕️ Тайный кофе", callback_data="activity_secret_coffee")],
        [InlineKeyboardButton("♟️ Шахматы", callback_data="activity_chess")],
        [InlineKeyboardButton("🏓 Настольный теннис", callback_data="activity_ping_pong")],
        [InlineKeyboardButton("📸 Фотоквесты", callback_data="activity_photo_quest")],
        [InlineKeyboardButton("🧠 Мастер-классы", callback_data="activity_workshop")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 *Главное меню ConnectBot*\n\n"
        "Выберите активность для участия:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_activity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора активности"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    activity_type = query.data.replace('activity_', '')
    
    # Сохраняем выбранную активность в контексте
    context.user_data['selected_activity'] = activity_type
    
    # Показываем меню управления активностью
    await show_activity_management(query, context, activity_type)

async def show_activity_management(query, context, activity_type):
    """Показать меню управления активностью"""
    from activities.services import ActivityManager
    from employees.models import Employee
    
    user_id = query.from_user.id
    activity_names = {
        'secret_coffee': '☕️ Тайный кофе',
        'chess': '♟️ Шахматы',
        'ping_pong': '🏓 Настольный теннис',
        'photo_quest': '📸 Фотоквесты',
        'workshop': '🧠 Мастер-классы',
    }
    
    activity_name = activity_names.get(activity_type, activity_type)
    
    # Проверяем статус подписки
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        manager = ActivityManager()
        
        # TODO: Реализовать проверку подписки
        is_subscribed = True  # Временная заглушка
        
        if is_subscribed:
            status_text = "✅ Вы подписаны на эту активность"
            button_text = "❌ Отписаться"
            callback_data = f"unsubscribe_{activity_type}"
        else:
            status_text = "❌ Вы не подписаны на эту активность"
            button_text = "✅ Подписаться"
            callback_data = f"subscribe_{activity_type}"
            
    except Employee.DoesNotExist:
        status_text = "⚠️ Сначала завершите регистрацию"
        button_text = "👤 Завершить регистрацию"
        callback_data = "complete_registration"
    
    keyboard = [
        [InlineKeyboardButton(button_text, callback_data=callback_data)],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{activity_type}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*{activity_name}*\n\n"
        f"{status_text}\n\n"
        "Управление участием:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подписки/отписки от активности"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('subscribe_'):
        activity_type = data.replace('subscribe_', '')
        # TODO: Реализовать логику подписки
        await query.edit_message_text("✅ Вы успешно подписались на активность!")
        
    elif data.startswith('unsubscribe_'):
        activity_type = data.replace('unsubscribe_', '')
        # TODO: Реализовать логику отписки
        await query.edit_message_text("❌ Вы отписались от активности.")
    
    # Возвращаемся в главное меню
    await show_main_menu(update, context)

def setup_menu_handlers(application):
    """Настройка обработчиков меню"""
    application.add_handler(CallbackQueryHandler(handle_activity_selection, pattern="^activity_"))
    application.add_handler(CallbackQueryHandler(handle_subscription, pattern="^(subscribe|unsubscribe)_"))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"))