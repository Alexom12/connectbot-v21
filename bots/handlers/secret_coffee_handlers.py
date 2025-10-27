import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from activities.services.anonymous_coffee_service import anonymous_coffee_service
from employees.models import Employee
from bots.utils.message_utils import reply_with_menu
from bots.menu_manager import MenuManager

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
            await reply_with_menu(update, "❌ Неверная команда. Используйте команду из уведомления.", menu_type='main')
            return
        
        # Получаем сотрудника
        employee = await Employee.objects.aget(telegram_id=user_id)
        
        # Начинаем планирование
        success, result = await anonymous_coffee_service.handle_meeting_scheduling(meeting_id, employee)
        
        if not success:
            await reply_with_menu(update, result, menu_type='main')
            return
        
        # Сохраняем данные в контексте
        context.user_data['current_meeting'] = {
            'meeting_id': meeting_id,
            'meeting': result['meeting'],
            'partner': result['partner'],
            'employee_code': result['employee_code'],
            'recognition_sign': result['recognition_sign']
        }
        
        coffee_text = f"""
🎭 *ПЛАНИРОВАНИЕ ТАЙНОЙ ВСТРЕЧИ*

🤫 Общайтесь через бота-посредника
📋 Ваш код: `{result['employee_code']}`
🎯 Опознавательный знак: *{result['recognition_sign']}*

Используйте кнопки ниже для управления встречей:
• 💬 Написать сообщение - отправить сообщение партнеру
• 📅 Предложить встречу - выбрать время для встречи
• 📋 Инструкция - правила и рекомендации
"""
        
        await reply_with_menu(update, coffee_text, menu_type='coffee', parse_mode='Markdown')
        
    except Employee.DoesNotExist:
        await reply_with_menu(update, "❌ Сначала завершите регистрацию в системе.", menu_type='main')
    except Exception as e:
        logger.error(f"❌ Ошибка начала планирования: {e}")
        await reply_with_menu(update, "❌ Произошла ошибка. Попробуйте позже.", menu_type='main')

async def handle_coffee_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений для пересылки"""
    user_id = update.effective_user.id
    
    if 'current_meeting' not in context.user_data:
        await reply_with_menu(update, "❌ Сначала начните планирование встречи через меню.", menu_type='coffee')
        return
    
    meeting_data = context.user_data['current_meeting']
    message_text = update.message.text
    
    # Отправляем сообщение через бота-посредника
    employee = await Employee.objects.aget(telegram_id=user_id)
    success = await anonymous_coffee_service.send_message_via_bot(
        meeting_data['meeting'], employee, message_text
    )
    
    if success:
        await reply_with_menu(update, "✅ Сообщение отправлено партнеру!", menu_type='coffee')
    else:
        await reply_with_menu(update, "❌ Ошибка отправки сообщения.", menu_type='coffee')

async def handle_coffee_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок (для обратной совместимости)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'coffee_send_message':
        message_text = """
💬 *ОТПРАВКА СООБЩЕНИЯ*

Напишите сообщение, и бот перешлет его вашему партнеру анонимно.

Партнер увидит только текст без вашего имени.

Просто напишите сообщение в чат и нажмите отправить.
"""
        await reply_with_menu(update, message_text, menu_type='coffee', parse_mode='Markdown')
        
    elif data == 'coffee_propose_meeting':
        await show_meeting_proposal_menu(query, context)
        
    elif data == 'coffee_emergency_stop':
        await handle_emergency_stop_request(query, context)
        
    elif data == 'coffee_instructions':
        await show_coffee_instructions(query, context)

async def show_meeting_proposal_menu(query, context):
    """Показать меню предложения встречи (для обратной совместимости)"""
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
    """Обработка запроса экстренной остановки (для обратной совместимости)"""
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
    """Показать инструкцию по Тайному кофе (для обратной совместимости)"""
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

async def handle_coffee_text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых команд для Тайного кофе через Reply клавиатуру"""
    text = update.message.text
    user_id = update.effective_user.id
    
    try:
        if text == "💬 Написать сообщение":
            message_help = """
💬 *Написать сообщение партнеру*

Просто напишите ваше сообщение в чат и нажмите отправить.

Бот автоматически перешлет его вашему партнеру анонимно.

💡 Сообщение будет доставлено без указания вашего имени.
"""
            await reply_with_menu(update, message_help, menu_type='coffee', parse_mode='Markdown')
            
        elif text == "📅 Предложить встречу":
            meeting_help = """
📅 *Предложить встречу*

Для предложения встречи используйте следующие форматы:

*Онлайн встречи:*
• "Понедельник 10:00-12:00 онлайн"
• "Среда 14:00-15:00 видеозвонок"

*Оффлайн встречи:*
• "Вторник 12:00-13:00 кафе на 1 этаже"
• "Четверг 16:00-17:00 переговорка 3.14"

💡 Вы можете предложить до 3 вариантов времени.
"""
            await reply_with_menu(update, meeting_help, menu_type='coffee', parse_mode='Markdown')
            
        elif text == "📋 Инструкция":
            instructions = """
📋 *Инструкция Тайного кофе*

🤫 *СОХРАНЯЙТЕ ТАЙНУ*
• Не раскрывайте свою личность
• Используйте только коды для общения

💬 *ОБЩЕНИЕ ЧЕРЕЗ БОТА*
• Все сообщения идут через посредника
• Бот сохраняет анонимность

🎯 *ПЛАНИРОВАНИЕ ВСТРЕЧИ*
1. Предложите время через бота
2. Партнер подтвердит или предложит другое
3. После подтверждения получите финальные инструкции

🚨 *БЕЗОПАСНОСТЬ*
• Используйте только официальные команды
• Все инциденты анонимно разбираются
• Модератор доступен 24/7
"""
            await reply_with_menu(update, instructions, menu_type='coffee', parse_mode='Markdown')
            
        elif text == "⬅️ Назад в меню":
            menu_text = await MenuManager.create_main_menu_message()
            await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')
            
        else:
            # Если это обычное сообщение и есть активная встреча, пересылаем его
            if 'current_meeting' in context.user_data:
                await handle_coffee_message(update, context)
            else:
                # Если нет активной встречи, показываем меню кофе
                coffee_text = await MenuManager.create_coffee_menu()
                await reply_with_menu(update, coffee_text, menu_type='coffee', parse_mode='Markdown')
                
    except Exception as e:
        logger.error(f"Ошибка обработки текстовой команды кофе: {e}")
        await reply_with_menu(update, "❌ Произошла ошибка. Попробуйте позже.", menu_type='main')

def setup_secret_coffee_handlers(application):
    """Настройка обработчиков Тайного кофе"""
    # Оставляем команду для обратной совместимости
    application.add_handler(CommandHandler("schedule_meeting", start_coffee_scheduling))
    
    # Обработчики callback для обратной совместимости
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^coffee_"))
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^prop_"))
    application.add_handler(CallbackQueryHandler(handle_coffee_callback, pattern="^emergency_"))
    
    # Обработчик текстовых сообщений для Тайного кофе через Reply клавиатуру
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            r'^(💬 Написать сообщение|📅 Предложить встречу|📋 Инструкция|⬅️ Назад в меню)$'
        ),
        handle_coffee_text_commands
    ))
    
    # Обработчик обычных текстовых сообщений (для пересылки)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_coffee_text_commands
    ))