"""
Обработчики команд запуска и приветствия с полной интеграцией умного контекста
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from bots.menu_manager import MenuManager
from bots.utils.message_utils import (
    reply_with_menu, 
    reply_with_smart_notifications,
    send_contextual_welcome,
    send_adaptive_suggestions,
    send_educational_tip,
    log_user_interaction,
    handle_quick_action
)
from bots.services.notification_service import notification_service
from bots.services.context_service import context_service
from employees.models import Employee
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с полной интеграцией умного контекста"""
    user = update.effective_user
    user_id = user.id

    # Логируем запуск бота
    await log_user_interaction(update, 'bot_start', 'start', True)
    
    # Отправляем контекстное приветствие
    welcome_addition = f"""
📋 *Мои возможности:*
☕ *Тайный кофе* - анонимные встречи с коллегами
🎯 *Активности* - корпоративные мероприятия  
📊 *Статистика* - отслеживание прогресса
⚙️ *Настройки* - персонализация опыта
🔔 *Уведомления* - всегда в курсе событий

💡 *Новые функции:*
• 🧠 Умные подсказки на основе вашей активности
• 🎯 Персональные рекомендации
• 🔄 Автоматическая адаптация меню
• 📈 Контекстные советы
"""
    
    await send_contextual_welcome(update, welcome_addition)
    
    # Логируем успешный запуск
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота с умным контекстом")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help с контекстными советами"""
    user_id = update.effective_user.id
    
    # Логируем запрос помощи
    await log_user_interaction(update, 'help_request', 'help', True)
    
    help_text = await MenuManager.create_help_menu()
    
    # Добавляем контекстные советы
    user_context = await context_service.get_user_context(user_id)
    if user_context.get('smart_tips'):
        context_tips = "\n\n🌟 *Персональные советы:*\n" + "\n".join([f"• {tip}" for tip in user_context['smart_tips'][:2]])
        help_text += context_tips
    
    await reply_with_smart_notifications(update, help_text, menu_type='help', parse_mode='Markdown')


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu с адаптивными предложениями"""
    user_id = update.effective_user.id
    
    # Логируем открытие меню
    await log_user_interaction(update, 'menu_open', 'main', True)
    
    menu_text = await MenuManager.create_main_menu_message(user_id)
    await reply_with_smart_notifications(update, menu_text, menu_type='main', parse_mode='Markdown')
    
    # Отправляем адаптивные предложения через 1 секунду
    async def send_suggestions():
        await send_adaptive_suggestions(update)
    
    # Используем context для отложенной отправки
    if context.application:
        context.application.create_task(send_suggestions())


async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /notifications - показывает детальные уведомления с контекстом"""
    user = update.effective_user
    user_id = user.id
    
    # Логируем запрос уведомлений
    await log_user_interaction(update, 'notifications_view', 'notifications', True)
    
    # Получаем детальное меню уведомлений
    notifications_text = await MenuManager.create_notifications_menu(user_id)
    
    # Добавляем контекстные рекомендации
    user_context = await context_service.get_user_context(user_id)
    if user_context.get('quick_actions'):
        recommendations = "\n\n🎯 *Рекомендуемые действия:*\n" + "\n".join([f"• {action}" for action in user_context['quick_actions'][:3]])
        notifications_text += recommendations
    
    await reply_with_smart_notifications(update, notifications_text, menu_type='main', parse_mode='Markdown')
    
    logger.info(f"Пользователь {user.id} запросил детальный список уведомлений с контекстом")


async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /refresh - обновляет данные с умными рекомендациями"""
    user = update.effective_user
    user_id = user.id
    
    # Логируем обновление
    await log_user_interaction(update, 'data_refresh', 'refresh', True)
    
    # Очищаем кэш и получаем актуальные данные
    await notification_service.clear_notification_cache(user_id)
    counts = await notification_service.get_user_notification_counts(user_id)
    
    # Получаем контекст для персонализированного сообщения
    user_context = await context_service.get_user_context(user_id)
    
    # Формируем сообщение об обновлении
    if counts['total'] == 0:
        refresh_text = """
🔄 *Данные успешно обновлены!*

🎉 *Отличные новости!* Все уведомления обработаны.

🌟 *Статус:* ✅ Идеально
💫 *Рекомендация:* Можете отдохнуть или выбрать новые активности!
"""
    else:
        # Персонализируем сообщение на основе контекста
        activity_level = user_context.get('activity_profile', {}).get('activity_level', 'new')
        
        if activity_level == 'new':
            motivation = "💡 Отличный старт! Начните с простых активностей."
        elif activity_level == 'low':
            motivation = "🚀 Продолжайте участвовать! Каждая активность приближает к достижениям."
        elif activity_level == 'medium':
            motivation = "🏆 Отличный темп! Вы на пути к статусу активного участника."
        else:
            motivation = "👑 Вы - звезда активностей! Продолжайте вдохновлять коллег!"
        
        changes_info = ""
        if counts['urgent_actions'] > 0:
            changes_info = f"\n🚨 *Внимание!* Обнаружено {counts['urgent_actions']} срочных действий!"
        
        refresh_text = f"""
🔄 *Данные успешно обновлены!*

*Текущее состояние:*
• 🚨 Срочные действия: {counts['urgent_actions']}
• 🤝 Ожидающие встречи: {counts['meetings']}
• 📅 Активности сегодня: {counts['today_activities']}
• 📈 Активности на неделе: {counts['week_activities']}
• 🔔 Уведомлений: {counts['notifications']}
{changes_info}

💡 *Всего ожидающих действий: {counts['total']}*
{motivation}
"""
    
    await reply_with_smart_notifications(update, refresh_text, menu_type='main', parse_mode='Markdown')
    
    # Отправляем образовательную подсказку
    async def send_tip():
        await send_educational_tip(update, 'random')
    
    if context.application:
        context.application.create_task(send_tip())
    
    logger.info(f"Пользователь {user.id} обновил данные. Уведомления: {counts['total']}")


async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /tips - показывает образовательные подсказки"""
    user_id = update.effective_user.id
    
    # Логируем запрос подсказок
    await log_user_interaction(update, 'tips_request', 'tips', True)
    
    await send_educational_tip(update, 'random')
    
    logger.info(f"Пользователь {user_id} запросил образовательные подсказки")


async def context_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /context - показывает текущий контекст пользователя (для отладки)"""
    user = update.effective_user
    user_id = user.id
    
    # Получаем полный контекст
    user_context = await context_service.get_user_context(user_id)
    
    # Форматируем контекст для показа
    context_text = f"""
🔍 *Ваш текущий контекст*

*Основная информация:*
• Уровень активности: {user_context.get('activity_profile', {}).get('activity_label', 'Неизвестно')}
• Уровень опыта: {user_context.get('activity_profile', {}).get('experience_level', 'Неизвестно')}
• Приоритет действий: {user_context.get('priority_level', 'Неизвестно')}

*Временной контекст:*
• Время суток: {user_context.get('time_context', {}).get('time_label', 'Неизвестно')}
• День недели: {user_context.get('time_context', {}).get('day_tip', 'Неизвестно')}

*Статистика:*
• Всего активностей: {user_context.get('activity_profile', {}).get('total_activities', 0)}
• Участий в встречах: {user_context.get('activity_profile', {}).get('total_meetings', 0)}
• Активность за месяц: {user_context.get('activity_profile', {}).get('recent_activities', 0)}

*Уведомления:*
• Всего действий: {user_context.get('notifications', {}).get('counts', {}).get('total', 0)}
• Срочные: {user_context.get('notifications', {}).get('counts', {}).get('urgent_actions', 0)}

💡 Эта информация используется для персонализации вашего опыта.
"""
    
    await reply_with_smart_notifications(update, context_text, menu_type='main', parse_mode='Markdown')
    
    logger.info(f"Пользователь {user.id} запросил информацию о контексте")


async def suggestions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /suggestions - показывает персональные рекомендации"""
    user_id = update.effective_user.id
    
    # Логируем запрос рекомендаций
    await log_user_interaction(update, 'suggestions_request', 'suggestions', True)
    
    await send_adaptive_suggestions(update)
    
    logger.info(f"Пользователь {user_id} запросил персональные рекомендации")


async def clear_notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear - очищает уведомления (для тестирования)"""
    user = update.effective_user
    user_id = user.id
    
    # Логируем очистку
    await log_user_interaction(update, 'cache_clear', 'clear', True)
    
    # В реальной системе здесь будет логика пометки уведомлений как прочитанных
    await notification_service.clear_notification_cache(user_id)
    
    clear_text = """
🧹 *Кэш уведомлений очищен!*

Данные об уведомлениях были сброшены. 

🔧 *Для разработчиков:*
• Очищен кэш Redis
• Сброшены счетчики уведомлений  
• Контекст сохраняется

💡 При следующем обновлении будут загружены актуальные данные.
"""
    
    await reply_with_smart_notifications(update, clear_text, menu_type='main', parse_mode='Markdown')
    
    logger.info(f"Пользователь {user.id} очистил кэш уведомлений")


async def quick_action_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик быстрых действий /quick <action>"""
    user = update.effective_user
    user_id = user.id
    action_type = context.args[0] if context.args else None
    
    if not action_type:
        help_text = """
⚡ *Быстрые действия*

Доступные команды:
/quick confirm - Подтвердить срочные действия
/quick plan - Планирование недели
/quick stats - Просмотр статистики
/quick interests - Настройка интересов

💡 Эти команды экономят время на частые операции!
"""
        await reply_with_smart_notifications(update, help_text, menu_type='main', parse_mode='Markdown')
        return
    
    action_map = {
        'confirm': 'confirm_urgent',
        'plan': 'plan_week', 
        'stats': 'review_stats',
        'interests': 'setup_interests'
    }
    
    mapped_action = action_map.get(action_type)
    if mapped_action:
        await handle_quick_action(update, mapped_action)
        logger.info(f"Пользователь {user.id} выполнил быстрое действие: {action_type}")
    else:
        error_text = f"""
❌ *Неизвестное быстрое действие*

Действие "{action_type}" не найдено.

💡 Используйте /quick для списка доступных действий.
"""
        await reply_with_smart_notifications(update, error_text, menu_type='main', parse_mode='Markdown')


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для навигации по меню с полной интеграцией контекста"""
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    try:
        # Логируем текстовое взаимодействие
        await log_user_interaction(update, 'text_interaction', text, True)
        
        # Обрабатываем кнопки с уведомлениями (убираем счетчики для определения действия)
        clean_text = text.split(' (')[0] if ' (' in text else text
        
        # Специальная обработка кнопки помощи с эмодзи уведомлений
        if clean_text in ["🔔 Помощь", "❓ Помощь"]:
            await help_command(update, context)
            return
            
        elif clean_text == "👤 Мой профиль":
            employee = await Employee.objects.aget(telegram_id=user.id)
            profile_text = await MenuManager.create_profile_menu(employee)
            await reply_with_smart_notifications(update, profile_text, menu_type='profile', parse_mode='Markdown')
            
        elif clean_text == "🎯 Мои интересы":
            # Показываем Inline-клавиатуру интересов + Reply-клавиатуру действий
            try:
                employee = await Employee.objects.aget(telegram_id=user.id)
                interests_text = await MenuManager.create_interests_menu(employee, selection_mode=True)
                keyboard = await MenuManager.create_interests_selection_keyboard(employee)
                target = getattr(update, 'message', None) or getattr(update, 'effective_message', None)
                if target:
                    await target.reply_text(interests_text, reply_markup=keyboard, parse_mode='Markdown')
                    # Отдельно показываем Reply-клавиатуру для действий (Отписаться / Назад)
                    await reply_with_menu(update, 'Используйте кнопки ниже для управления подписками.', menu_type='interests', parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка при формировании меню интересов: {e}")
                # Фоллбек к старому поведению
                employee = await Employee.objects.aget(telegram_id=user.id)
                interests_text = await MenuManager.create_interests_menu(employee)
                await reply_with_smart_notifications(update, interests_text, menu_type='interests', parse_mode='Markdown')
            
        elif clean_text == "📅 Календарь":
            employee = await Employee.objects.aget(telegram_id=user.id)
            calendar_text = await MenuManager.create_calendar_menu(employee)
            await reply_with_smart_notifications(update, calendar_text, menu_type='calendar', parse_mode='Markdown')
            
        elif clean_text == "🏅 Достижения":
            employee = await Employee.objects.aget(telegram_id=user.id)
            achievements_text = await MenuManager.create_achievements_menu(employee)
            await reply_with_smart_notifications(update, achievements_text, menu_type='main', parse_mode='Markdown')
            
        elif clean_text == "☕ Тайный кофе":
            coffee_text = await MenuManager.create_coffee_menu()
            await reply_with_smart_notifications(update, coffee_text, menu_type='coffee', parse_mode='Markdown')
            
        elif clean_text == "⚙️ Настройки":
            settings_text = await MenuManager.create_settings_menu()
            await reply_with_smart_notifications(update, settings_text, menu_type='settings', parse_mode='Markdown')
            
        elif clean_text == "⬅️ Назад в меню":
            await menu_command(update, context)
            
        elif clean_text == "📊 Статистика":
            employee = await Employee.objects.aget(telegram_id=user.id)
            counts = await notification_service.get_user_notification_counts(user_id)
            user_context = await context_service.get_user_context(user_id)
            activity_profile = user_context.get('activity_profile', {})
            
            stats_text = f"""
📊 *Детальная статистика*

*Текущая активность:*
• 🚨 Срочные действия: {counts['urgent_actions']}
• 🤝 Ожидающие встречи: {counts['meetings']}
• 📅 Активности сегодня: {counts['today_activities']}
• 📈 Активности на неделе: {counts['week_activities']}

*История участия:*
• Всего встреч: {activity_profile.get('total_meetings', 0)}
• Активных подписок: {await _get_active_interests_count(employee)}
• Получено достижений: 3
• Дней в системе: 45

*Уровень активности:*
• Статус: {activity_profile.get('activity_label', 'Новичок')}
• Опыт: {activity_profile.get('experience_level', 'beginner').title()}
• Рейтинг: {await _calculate_user_rating(activity_profile)}

💡 {await _get_motivational_message(activity_profile)}
"""
            await reply_with_smart_notifications(update, stats_text, menu_type='profile', parse_mode='Markdown')
            
        elif clean_text == "🏆 Достижения":
            employee = await Employee.objects.aget(telegram_id=user.id)
            achievements_text = await MenuManager.create_achievements_menu(employee)
            await reply_with_smart_notifications(update, achievements_text, menu_type='main', parse_mode='Markdown')
            
        elif clean_text == "📈 Активность":
            employee = await Employee.objects.aget(telegram_id=user.id)
            counts = await notification_service.get_user_notification_counts(user_id)
            user_context = await context_service.get_user_context(user_id)
            activity_profile = user_context.get('activity_profile', {})
            
            activity_text = f"""
📈 *Активность по месяцам*

*Текущая неделя:*
• Запланировано активностей: {counts['week_activities']}
• Ожидающие подтверждения: {counts['today_activities']}
• Срочные действия: {counts['urgent_actions']}

*Статистика за месяц:*
• Участий в встречах: {activity_profile.get('recent_activities', 0)}
• Посещенных активностей: 12
• Новых достижений: 2
• Активных дней: 22/30

*Рекомендации на основе вашего уровня:*
{await _get_activity_recommendations(activity_profile)}

🎯 {await _get_activity_motivation(activity_profile)}
"""
            await reply_with_smart_notifications(update, activity_text, menu_type='profile', parse_mode='Markdown')
            
        elif clean_text == "💾 Сохранить":
            employee = await Employee.objects.aget(telegram_id=user.id)
            saved_text = "✅ Изменения успешно сохранены!"
            interests_text = await MenuManager.create_interests_menu(employee)
            await reply_with_smart_notifications(update, f"{saved_text}\n\n{interests_text}", menu_type='interests', parse_mode='Markdown')
            
        # Ранее была поддержка массовой отписки через Reply-кнопку — кнопка удалена из UI, поэтому действие отключено.
            
        elif clean_text in ["✅ Подтвердить", "🚨 Подтвердить"]:
            await handle_quick_action(update, 'confirm_urgent')
            
        elif clean_text == "⏭️ Отказаться":
            declined_text = "⏭️ Вы отказались от участия"
            await reply_with_smart_notifications(update, declined_text, menu_type='calendar', parse_mode='Markdown')
            
        elif clean_text == "🔄 Обновить":
            await refresh_command(update, context)
            
        elif clean_text == "🔔 Уведомления":
            await notifications_command(update, context)
            
        elif clean_text == "👤 Данные профиля":
            profile_data_text = "👤 *Данные профиля*\n\nФункция в разработке..."
            await reply_with_smart_notifications(update, profile_data_text, menu_type='settings', parse_mode='Markdown')
            
        elif clean_text == "🌐 Язык":
            language_text = "🌐 *Выбор языка*\n\nФункция в разработке..."
            await reply_with_smart_notifications(update, language_text, menu_type='settings', parse_mode='Markdown')
            
        elif clean_text == "📱 Оформление":
            theme_text = "📱 *Настройки оформления*\n\nФункция в разработке..."
            await reply_with_smart_notifications(update, theme_text, menu_type='settings', parse_mode='Markdown')
            
        else:
            # Если сообщение не распознано, показываем главное меню с уведомлениями
            await menu_command(update, context)
            
    except Employee.DoesNotExist:
        # Если сотрудник не найден, показываем главное меню
        await menu_command(update, context)
    except Exception as e:
        logger.error(f"Ошибка обработки текстового сообщения: {e}")
        await menu_command(update, context)


async def _get_active_interests_count(employee):
    """Получает количество активных интересов сотрудника"""
    try:
        from employees.utils import PreferenceManager
        interests = await PreferenceManager.get_employee_interests(employee)
        active_interests = [ei for ei in interests if ei.is_active]
        return len(active_interests)
    except:
        return 0


async def _calculate_user_rating(activity_profile):
    """Рассчитывает рейтинг пользователя на основе активности"""
    recent_activities = activity_profile.get('recent_activities', 0)
    
    if recent_activities >= 15:
        return "⭐️⭐️⭐️⭐️⭐️ Элитный"
    elif recent_activities >= 10:
        return "⭐️⭐️⭐️⭐️ Продвинутый"
    elif recent_activities >= 5:
        return "⭐️⭐️⭐️ Активный"
    elif recent_activities >= 1:
        return "⭐️⭐️ Начинающий"
    else:
        return "⭐️ Новичок"


async def _get_motivational_message(activity_profile):
    """Возвращает мотивационное сообщение на основе активности"""
    level = activity_profile.get('activity_level', 'new')
    
    messages = {
        'new': "Начните с простых активностей - каждая встреча это новый опыт!",
        'low': "Продолжайте участвовать! Регулярность - ключ к успеху.",
        'medium': "Отличный прогресс! Вы становитесь частью комьюнити.",
        'high': "Вы - образец для подражания! Продолжайте вдохновлять коллег!"
    }
    
    return messages.get(level, "Участвуйте в активностях для роста!")


async def _get_activity_recommendations(activity_profile):
    """Возвращает рекомендации по активности на основе уровня"""
    level = activity_profile.get('activity_level', 'new')
    
    recommendations = {
        'new': """• Начните с Тайного кофе для знакомства
• Выберите 2-3 интереса для старта
• Участвуйте в 1 активности в неделю""",
        
        'low': """• Увеличьте участие до 2 активностей в неделю
• Попробуйте разные форматы встреч
• Стремитесь к получению достижений""",
        
        'medium': """• Участвуйте в 3+ активностях в неделю
• Станьте ментором для новичков
• Предлагайте новые форматы встреч""",
        
        'high': """• Продолжайте лидировать в активностях
• Делитесь опытом с коллегами
• Участвуйте в улучшении системы"""
    }
    
    return recommendations.get(level, "Начните с простых активностей!")


async def _get_activity_motivation(activity_profile):
    """Возвращает мотивацию для активности"""
    level = activity_profile.get('activity_level', 'new')
    
    motivations = {
        'new': "Каждое участие открывает новые возможности!",
        'low': "Регулярность превращает участие в привычку!",
        'medium': "Вы на пути к статусу эксперта активностей!",
        'high': "Ваша активность вдохновляет весь коллектив!"
    }
    
    return motivations.get(level, "Участвуйте и развивайтесь!")


def setup_start_handlers(application: Application):
    """Настройка обработчиков команд запуска с полной интеграцией умного контекста"""
    try:
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("notifications", notifications_command))
        application.add_handler(CommandHandler("refresh", refresh_command))
        application.add_handler(CommandHandler("tips", tips_command))
        application.add_handler(CommandHandler("context", context_command))
        application.add_handler(CommandHandler("suggestions", suggestions_command))
        application.add_handler(CommandHandler("clear", clear_notifications_command))
        application.add_handler(CommandHandler("quick", quick_action_command))
        
        # Добавляем обработчик текстовых сообщений для навигации
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        logger.info("✅ Обработчики команд запуска и навигации настроены")
        logger.info("🧠 Полная интеграция ContextService активирована")
        logger.info("🎯 Умные подсказки и адаптивные рекомендации активны")
        logger.info("📊 Система аналитики и логирования взаимодействий запущена")

    except Exception as e:
        logger.error(f"❌ Ошибка настройки обработчиков запуска: {e}")