import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from activities.services.preference_service import preference_service
from employees.models import Employee

logger = logging.getLogger(__name__)

async def show_preferences_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настройки предпочтений"""
    user_id = update.effective_user.id
    
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        preferences = await preference_service.get_or_create_preferences(employee)
        
        keyboard = [
            [InlineKeyboardButton("🕐 Настроить доступность", callback_data="pref_availability")],
            [InlineKeyboardButton("💻 Формат встреч", callback_data="pref_format")],
            [InlineKeyboardButton("🎯 Темы для разговора", callback_data="pref_topics")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_settings = f"""
*ТЕКУЩИЕ НАСТРОЙКИ:*

🕐 *Доступность:* {len(preferences.availability_slots)} слотов
💻 *Формат:* {preferences.get_preferred_format_display()}
🎯 *Интересы:* {', '.join(preferences.topics_of_interest[:3])}{'...' if len(preferences.topics_of_interest) > 3 else ''}
"""
        
        await update.message.reply_text(
            f"⚙️ *НАСТРОЙКИ ТАЙНОГО КОФЕ*\n\n{current_settings}\nВыберите настройку:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Employee.DoesNotExist:
        await update.message.reply_text("❌ Сначала завершите регистрацию в системе.")
    except Exception as e:
        logger.error(f"❌ Ошибка показа настроек: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def handle_preference_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок настроек"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        
        if data == 'pref_availability':
            await show_availability_settings(query, context, employee)
        elif data == 'pref_format':
            await show_format_settings(query, context, employee)
        elif data == 'pref_topics':
            await show_topics_settings(query, context, employee)
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки предпочтений: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

async def show_availability_settings(query, context, employee):
    """Показать настройки доступности"""
    preferences = await preference_service.get_or_create_preferences(employee)
    
    keyboard = [
        [InlineKeyboardButton("🕐 Пн 10:00-12:00", callback_data="avail_mon_10")],
        [InlineKeyboardButton("🕐 Пн 14:00-16:00", callback_data="avail_mon_14")],
        [InlineKeyboardButton("🕐 Вт 10:00-12:00", callback_data="avail_tue_10")],
        [InlineKeyboardButton("🕐 Вт 14:00-16:00", callback_data="avail_tue_14")],
        [InlineKeyboardButton("🕐 Ср 12:00-14:00", callback_data="avail_wed_12")],
        [InlineKeyboardButton("🕐 Чт 16:00-18:00", callback_data="avail_thu_16")],
        [InlineKeyboardButton("🕐 Пт 11:00-13:00", callback_data="avail_fri_11")],
        [InlineKeyboardButton("✅ Сохранить", callback_data="avail_save")],
        [InlineKeyboardButton("🔙 Назад", callback_data="pref_back")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Показываем текущие выбранные слоты
    current_slots = "\n".join([f"✅ {slot}" for slot in preferences.availability_slots])
    
    await query.edit_message_text(
        f"🕐 *НАСТРОЙКА ДОСТУПНОСТИ*\n\n"
        f"Выберите удобные временные слоты:\n\n"
        f"*Текущие слоты:*\n{current_slots if current_slots else '❌ Не настроено'}\n\n"
        f"ℹ️ Выберите слоты, когда вы обычно свободны для кофе-встреч.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_format_settings(query, context, employee):
    """Показать настройки формата встреч"""
    preferences = await preference_service.get_or_create_preferences(employee)
    
    keyboard = [
        [InlineKeyboardButton("💻 Только онлайн", callback_data="format_online")],
        [InlineKeyboardButton("🏢 Только оффлайн", callback_data="format_offline")],
        [InlineKeyboardButton("💻🏢 Оба формата", callback_data="format_both")],
        [InlineKeyboardButton("🔙 Назад", callback_data="pref_back")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💻 *ФОРМАТ ВСТРЕЧ*\n\n"
        f"*Текущий формат:* {preferences.get_preferred_format_display()}\n\n"
        f"Выберите предпочтительный формат встреч:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_topics_settings(query, context, employee):
    """Показать настройки тем для разговора"""
    preferences = await preference_service.get_or_create_preferences(employee)
    
    keyboard = [
        [InlineKeyboardButton("💼 Работа и карьера", callback_data="topic_work")],
        [InlineKeyboardButton("🎨 Хобби и увлечения", callback_data="topic_hobby")],
        [InlineKeyboardButton("✈️ Путешествия", callback_data="topic_travel")],
        [InlineKeyboardButton("📚 Книги и фильмы", callback_data="topic_books")],
        [InlineKeyboardButton("🏃 Спорт и здоровье", callback_data="topic_sport")],
        [InlineKeyboardButton("🔬 Технологии", callback_data="topic_tech")],
        [InlineKeyboardButton("✅ Сохранить", callback_data="topics_save")],
        [InlineKeyboardButton("🔙 Назад", callback_data="pref_back")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_topics = ", ".join(preferences.topics_of_interest)
    
    await query.edit_message_text(
        f"🎯 *ТЕМЫ ДЛЯ РАЗГОВОРА*\n\n"
        f"*Текущие темы:* {current_topics}\n\n"
        f"Выберите интересные вам темы для общения:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def setup_preference_handlers(application):
    """Настройка обработчиков предпочтений"""
    application.add_handler(CommandHandler("preferences", show_preferences_menu))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^pref_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^avail_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^format_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^topic_"))