import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from activities.services.preference_service import preference_service
from employees.models import Employee
from employees.utils import PreferenceManager
from bots.services.redis_service import redis_service
from asgiref.sync import sync_to_async
from bots.utils.message_utils import reply_with_menu
from bots.menu_manager import MenuManager

logger = logging.getLogger(__name__)

async def show_preferences_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню настройки предпочтений через Reply клавиатуру"""
    user_id = update.effective_user.id
    
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        preferences = await preference_service.get_or_create_preferences(employee)
        
        current_settings = f"""
*ТЕКУЩИЕ НАСТРОЙКИ:*

🕐 *Доступность:* {len(preferences.availability_slots)} слотов
💻 *Формат:* {preferences.get_preferred_format_display()}
🎯 *Интересы:* {', '.join(preferences.topics_of_interest[:3])}{'...' if len(preferences.topics_of_interest) > 3 else ''}

Для управления настройками используйте кнопки ниже:
• 🎯 Мои интересы - управление подписками
• ⚙️ Настройки - общие настройки бота
"""
        
        await reply_with_menu(update, current_settings, menu_type='interests', parse_mode='Markdown')
        
    except Employee.DoesNotExist:
        await reply_with_menu(update, "❌ Сначала завершите регистрацию в системе.", menu_type='main')
    except Exception as e:
        logger.error(f"❌ Ошибка показа настроек: {e}")
        await reply_with_menu(update, "❌ Произошла ошибка. Попробуйте позже.", menu_type='main')

async def handle_preference_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от кнопок настроек (для обратной совместимости)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        
        # Existing preference menu actions
        if data == 'pref_availability':
            await show_availability_settings(query, context, employee)
        elif data == 'pref_format':
            await show_format_settings(query, context, employee)
        elif data == 'pref_topics':
            await show_topics_settings(query, context, employee)
        
        # Toggle individual interest from menu_manager — выполняем мгновенное переключение в профиле
        elif data.startswith('toggle_interest_'):
            interest_code = data.replace('toggle_interest_', '')
            try:
                # Получаем текущее состояние и переключаем
                current_eis = await PreferenceManager.get_employee_interests(employee)
                current_active = {ei.interest.code for ei in current_eis if ei.is_active}

                if interest_code in current_active:
                    new_active = current_active - {interest_code}
                    action = 'removed'
                else:
                    new_active = current_active | {interest_code}
                    action = 'added'

                success = await PreferenceManager.update_employee_interests(employee, list(new_active))

                # Инвалидируем кеш сотрудника
                try:
                    from employees.redis_utils import RedisManager
                    RedisManager.invalidate_employee_cache(employee.id)
                except Exception:
                    logger.debug('INTERESTS_DEBUG: Не удалось инвалидировать кеш сотрудника после toggle interest')

                if success:
                    # Обновляем текст и клавиатуру (редактируем сообщение с InlineKeyboard)
                    interests_text = await MenuManager.create_interests_menu(employee, selection_mode=True)
                    new_keyboard = await MenuManager.create_interests_selection_keyboard(employee)
                    try:
                        await query.edit_message_text(interests_text, reply_markup=new_keyboard, parse_mode='Markdown')
                    except Exception:
                        # fallback — ответить коротким уведомлением
                        await query.answer(f"{'ВКЛ' if action=='added' else 'ВЫКЛ'}: {interest_code}", show_alert=False)
                else:
                    await query.answer('Ошибка при переключении подписки', show_alert=True)
            except Exception as e:
                logger.exception(f"Ошибка при toggle interest {interest_code} для user {user_id}: {e}")
                await query.answer('Произошла ошибка', show_alert=True)

        # Save pending interests — confirmation button. Previously read pending_interests from context
        # which was never populated when we used immediate toggle; to avoid accidentally clearing
        # subscriptions we now just re-read current active interests from DB and acknowledge.
        elif data == 'save_interests':
            try:
                current_eis = await PreferenceManager.get_employee_interests(employee)
                active_codes = [ei.interest.code for ei in current_eis if ei.is_active]
                # Call update with the same set (idempotent) to ensure DB/cache consistency
                success = await PreferenceManager.update_employee_interests(employee, active_codes)
                if success:
                    await query.answer('Изменения сохранены', show_alert=True)
                    # Refresh menu
                    interests_text = await MenuManager.create_interests_menu(employee)
                    await reply_with_menu(update, interests_text, menu_type='interests', parse_mode='Markdown')
                else:
                    await query.answer('Ошибка при сохранении', show_alert=True)
            except Exception as e:
                logger.error(f"Ошибка при сохранении интересов: {e}")
                await query.answer('Ошибка при сохранении', show_alert=True)

        elif data == 'disable_all_interests':
            # Ask for confirmation via edit
            keyboard = [
                [InlineKeyboardButton("Да, отписаться", callback_data="confirm_disable_all")],
                [InlineKeyboardButton("Отмена", callback_data="pref_back")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Вы уверены, что хотите отписаться от всех интересов?", reply_markup=reply_markup)
        elif data == 'confirm_disable_all':
            try:
                success = await PreferenceManager.disable_all_interests(employee)
                if success:
                    # invalidate cache already happens in disable_all_interests
                    await query.edit_message_text('Вы отписаны от всех интересов.')
                else:
                    await query.answer('Ошибка при отписке', show_alert=True)
            except Exception as e:
                logger.exception(f"Ошибка при confirm_disable_all для user {user_id}: {e}")
                await query.answer('Произошла ошибка', show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки предпочтений: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")

async def show_availability_settings(query, context, employee):
    """Показать настройки доступности (для обратной совместимости)"""
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
    """Показать настройки формата встреч (для обратной совместимости)"""
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
    """Показать настройки тем для разговора (для обратной совместимости)"""
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

async def handle_text_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для управления предпочтениями (фоллбек для текстовых команд).

    Теперь выбор интересов реализован через InlineKeyboard и обрабатывается в `handle_preference_callback`.
    Этот хэндлер оставлен для совместимости: по текстовой команде показывает меню интересов.
    """
    text = update.message.text
    user_id = update.effective_user.id

    try:
        employee = await Employee.objects.aget(telegram_id=user_id)

        # Если пользователь явно запросил меню интересов — показываем Inline меню
        if text and text.strip() == "🎯 Мои интересы":
            interests_text = await MenuManager.create_interests_menu(employee, selection_mode=True)
            keyboard = await MenuManager.create_interests_selection_keyboard(employee)
            target = getattr(update, 'message', None) or getattr(update, 'effective_message', None)
            if target:
                await target.reply_text(interests_text, reply_markup=keyboard, parse_mode='Markdown')
                # Показываем Reply-клавиатуру для действий (Отписаться / Назад)
                await reply_with_menu(update, 'Используйте кнопки ниже для управления подписками.', menu_type='interests', parse_mode='Markdown')
            return

        # Ранее тут была кнопка "🚫 Отписаться от всего" — удалена из UI, поэтому обработка снята.

        if text and text.strip() == '⬅️ Назад в меню':
            return await reply_with_menu(update, 'Возврат в главное меню', menu_type='main', parse_mode='Markdown')

        # Иначе — показываем общее меню интересов как фоллбек
        interests_text = await MenuManager.create_interests_menu(employee)
        keyboard = await MenuManager.create_interests_selection_keyboard(employee)
        target = getattr(update, 'message', None) or getattr(update, 'effective_message', None)
        if target:
            await target.reply_text(interests_text, reply_markup=keyboard, parse_mode='Markdown')
            # Показываем Reply-клавиатуру для действий (Отписаться / Назад)
            await reply_with_menu(update, 'Используйте кнопки выше для управления подписками.', menu_type='interests', parse_mode='Markdown')
            
    except Employee.DoesNotExist:
        await reply_with_menu(update, "❌ Сначала завершите регистрацию в системе.", menu_type='main')
    except Exception as e:
        logger.error(f"Ошибка обработки текстовых предпочтений: {e}")
        await reply_with_menu(update, "❌ Произошла ошибка. Попробуйте позже.", menu_type='main')

def setup_preference_handlers(application):
    """Настройка обработчиков предпочтений"""
    # Оставляем команду для обратной совместимости
    application.add_handler(CommandHandler("preferences", show_preferences_menu))
    
    # Обработчики callback для обратной совместимости
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^pref_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^avail_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^format_"))
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^topic_"))
    
    # Interest toggles and actions from menu_manager
    application.add_handler(CallbackQueryHandler(handle_preference_callback, pattern="^toggle_interest_"))
    # Inline callbacks only for toggle_interest (save/disable handled via ReplyKeyboard text handlers)
    # Обработчик текстовых сообщений для меню интересов (ReplyKeyboard кнопки)
    # Регистрируем конкретные текстовые команды, чтобы они не попали в общий навигационный обработчик
    try:
        application.add_handler(MessageHandler(filters.Regex(r'^(🎯 Мои интересы|⬅️ Назад в меню)$') & ~filters.COMMAND, handle_text_preferences))
    except Exception:
        # На некоторых версиях PTB filters.Regex может отличаться; используем fallback на простой текстовый фильтр
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_preferences))
    
    # Для выбора интересов используем InlineKeyboard — callbacks обрабатываются в handle_preference_callback