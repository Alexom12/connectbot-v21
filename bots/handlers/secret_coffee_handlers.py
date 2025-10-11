import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from activities.services.anonymous_coffee_service import anonymous_coffee_service
from employees.models import Employee

logger = logging.getLogger(__name__)

async def start_coffee_scheduling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало планирования встречи"""
    try:
        user_id = update.effective_user.id
        command = update.message.text
        
        # Извлекаем meeting_id из команды
        if '_' in command:
            meeting_id = command.split('_')[-1]
        else:
            await update.message.reply_text("❌ Неверная команда. Используйте команду из уведомления.")
            return
        
        # Получаем сотрудника
        employee = await Employee.objects.aget(telegram_id=user_id)
        
        # Начинаем планирование
        success, result = await anonymous_coffee_service.handle_meeting_scheduling(meeting_id, employee)
        
        if not success:
            await update.message.reply_text(result)
            return
        
        # Сохраняем данные в контексте
        context.user_data['current_meeting'] = {
            'meeting_id': meeting_id,
            'meeting': result['meeting'],
            'partner': result['partner'],
            'employee_code': result['employee_code'],
            'recognition_sign': result['recognition_sign']
        }
        
        # Показываем меню планирования
        keyboard = [
            [InlineKeyboardButton("💬 Написать сообщение", callback_data="coffee_send_message")],
            [InlineKeyboardButton("📅 Предложить встречу", callback_data="coffee_propose_meeting")],
            [InlineKeyboardButton("❌ Экстренная остановка", callback_data="coffee_emergency_stop")],
            [InlineKeyboardButton("📋 Инструкция", callback_data="coffee_instructions")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"""🎭 *ПЛАНИРОВАНИЕ ТАЙНОЙ ВСТРЕЧИ*

🤫 Общайтесь через бота-посредника
📋 Ваш код: `{result['employee_code']}`
🎯 Опознавательный знак: *{result['recognition_sign']}*

Выберите действие:""",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Employee.DoesNotExist:
        await update.message.reply_text("❌ Сначала завершите регистрацию в системе.")
    except Exception as e:
        logger.error(f"❌ Ошибка начала планирования: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def handle_coffee_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений для пересылки"""
    user_id = update.effective_user.id
    
    if 'current_meeting' not in context.user_data:
        await update.message.reply_text("❌ Сначала начните планирование встречи через меню.")
        return
    
    meeting_data = context.user_data['current_meeting']
    message_text = update.message.text
    
    # Отправляем сообщение через бота-посредника
    employee = await Employee.objects.aget(telegram_id=user_id)
    success = await anonymous_coffee_service.send_message_via_bot(
        meeting_data['meeting'], employee, message_text
    )
    
    if success:
        await update.message.reply_text("✅ Сообщение отправлено партнеру!")
    else:
        await update.message.reply_text("❌ Ошибка отправки сообщения.")

async def handle_coffee_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'coffee_send_message':
        await query.edit_message_text(
            "💬 *ОТПРАВКА СООБЩЕНИЯ*\n\n"
            "Напишите сообщение, и бот перешлет его вашему партнеру анонимно.\n\n"
            "Партнер увидит только текст без вашего имени.",
            parse_mode='Markdown'
        )
        
    elif data == 'coffee_propose_meeting':
        await show_meeting_proposal_menu(query, context)
        
    elif data == 'coffee_emergency_stop':
        await handle_emergency_stop_request(query, context)
        
    elif data == 'coffee_instructions':
        await show_coffee_instructions(query, context)

async def show_meeting_proposal_menu(query, context):
    """Показать меню предложения встречи"""
    meeting_data = context.user_data['current_meeting']
    
    keyboard = [
        [InlineKeyboardButton("🕐 Понедельник 10:00-12:00", callback_data="prop_mon_10")],
        [InlineKeyboardButton("🕐 Вторник 14:00-16:00", callback_data="prop_tue_14")],
        [InlineKeyboardButton("🕐 Среда 12:00-14:00", callback_data="prop_wed_12")],
        [InlineKeyboardButton("🕐 Четверг 16:00-18:00", callback_data="prop_thu_16")],
        [InlineKeyboardButton("🕐 Пятница 11:00-13:00", callback_data="prop_fri_11")],
        [InlineKeyboardButton("🔙 Назад", callback_data="coffee_back")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 *ПРЕДЛОЖЕНИЕ ВСТРЕЧИ*\n\n"
        "Выберите удобный временной слот:\n"
        "(Вы можете предложить до 3 вариантов)",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_emergency_stop_request(query, context):
    """Обработка запроса экстренной остановки"""
    keyboard = [
        [InlineKeyboardButton("✅ Да, остановить", callback_data="emergency_confirm")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data="coffee_back")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🚨 *ЭКСТРЕННАЯ ОСТАНОВКА*\n\n"
        "Вы уверены, что хотите остановить встречу?\n\n"
        "⚠️ Это действие:\n"
        "• Немедленно прекратит встречу\n"
        "• Уведомит модератора\n"
        "• Будет анонимно разобрано\n\n"
        "Используйте только в крайних случаях!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_coffee_instructions(query, context):
    """Показать инструкцию по Тайному кофе"""
    meeting_data = context.user_data['current_meeting']
    
    instructions = f"""🎭 *ИНСТРУКЦИЯ ТАЙНОГО КОФЕ*

🤫 *СОХРАНЯЙТЕ ТАЙНУ*
• Не раскрывайте свою личность
• Не пытайтесь узнать партнера заранее
• Используйте только коды для общения

💬 *ОБЩЕНИЕ ЧЕРЕЗ БОТА*
• Все сообщения идут через посредника
• Бот сохраняет анонимность
• Макс. 3 предложения встречи от каждого

📅 *ПЛАНИРОВАНИЕ ВСТРЕЧИ*
1. Предложите время/место через бота
2. Партнер подтвердит или предложит другое
3. После подтверждения получите финальные инструкции

🎯 *ОПОЗНАНИЕ НА МЕСТЕ*
• Ваш код: `{meeting_data['employee_code']}`
• Опознавательный знак: *{meeting_data['recognition_sign']}*
• Фото (за 5 мин до встречи, если разрешено)

🚨 *БЕЗОПАСНОСТЬ*
• /emergency_stop - экстренная остановка
• Все инциденты анонимно разбираются
• Модератор доступен 24/7

Удачи в вашем тайном приключении! 🎪"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="coffee_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instructions, reply_markup=reply_markup, parse_mode='Markdown')

def setup_secret_coffee_handlers(application):
    """Настройка обработчиков Тайного кофе"""
    application.add_handler(CommandHandler("schedule_meeting", start_coffee_scheduling))
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^coffee_"))
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^prop_"))
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^emergency_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coffee_message))