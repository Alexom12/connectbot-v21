from bots.menu_manager import MenuManager
from bots.utils.retry_utils import async_retry_decorator
from bots.services.notification_service import notification_service
from bots.services.context_service import context_service
from telegram.error import NetworkError, TimedOut
import logging

logger = logging.getLogger(__name__)


@async_retry_decorator(attempts=3, min_wait=1, max_wait=8, retry_exceptions=(NetworkError, TimedOut))
async def _send_with_keyboard(target, text, keyboard, parse_mode=None):
    return await target.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode)


@async_retry_decorator(attempts=2, min_wait=0.5, max_wait=4, retry_exceptions=(NetworkError, TimedOut))
async def _send_without_keyboard(target, text, parse_mode=None):
    return await target.reply_text(text, parse_mode=parse_mode)


async def reply_with_menu(update, text, menu_type='main', parse_mode=None, user_id=None, context_data=None):
    """Отправляет сообщение с соответствующей Reply клавиатурой меню и уведомлениями"""
    try:
        # Если user_id не передан, пытаемся извлечь из update
        if user_id is None:
            user_id = getattr(update.effective_user, 'id', None)
        
        # Получаем контекст пользователя для умных подсказок
        user_context = None
        if user_id:
            user_context = await context_service.get_user_context(user_id)
            # Нормализуем контекст в словарь, чтобы избежать AttributeError
            if not isinstance(user_context, dict):
                user_context = {}

            # Добавляем контекстные подсказки к тексту
            if context_data is None or not isinstance(context_data, dict):
                context_data = {}

            # Добавляем умные подсказки из контекста
            if user_context.get('smart_tips'):
                tips_to_show = user_context['smart_tips'][:2]  # Показываем до 2 подсказок
                if tips_to_show:
                    text += "\n\n💡 " + "\n💡 ".join(tips_to_show)
        
        # Получаем соответствующую клавиатуру с уведомлениями
        reply_markup = await MenuManager.get_reply_keyboard_for_menu(menu_type, user_id)
    except Exception as e:
        logger.error(f"Ошибка создания клавиатуры: {e}")
        reply_markup = await MenuManager.create_main_reply_keyboard(user_id)

    target = getattr(update, 'message', None) or getattr(update, 'effective_message', None)
    if not target:
        return

    try:
        return await _send_with_keyboard(target, text, reply_markup, parse_mode=parse_mode)
    except Exception:
        # Fallback: try sending without keyboard
        try:
            return await _send_without_keyboard(target, text, parse_mode=parse_mode)
        except Exception:
            return


async def reply_with_footer(update, text, parse_mode=None):
    """Reply to a message with a footer menu attached.

    Use tenacity-based retries for transient network errors. If sending with footer
    fails, fallback to sending without footer.
    """
    try:
        # Используем основную Reply клавиатуру вместо Inline кнопок
        user_id = getattr(update.effective_user, 'id', None)
        reply_markup = await MenuManager.create_main_reply_keyboard(user_id)
    except Exception:
        reply_markup = None

    target = getattr(update, 'message', None) or getattr(update, 'effective_message', None)
    if not target:
        return

    if reply_markup:
        try:
            return await _send_with_keyboard(target, text, reply_markup, parse_mode=parse_mode)
        except Exception:
            # Fallback: try sending without keyboard
            try:
                return await _send_without_keyboard(target, text, parse_mode=parse_mode)
            except Exception:
                return
    else:
        try:
            return await _send_without_keyboard(target, text, parse_mode=parse_mode)
        except Exception:
            return


async def reply_with_smart_notifications(update, text, menu_type='main', parse_mode=None, context_data=None, user_id=None):
    """Умная отправка сообщений с контекстными уведомлениями и подсказками

    Принимает опциональный user_id — некоторые вызовы работают из threaded contexts
    и передают user_id явно.
    """
    try:
        if user_id is None:
            user_id = getattr(update.effective_user, 'id', None)
    except Exception:
        user_id = None
    
    # Получаем расширенный контекст пользователя
    user_context = None
    if user_id:
        try:
            user_context = await context_service.get_user_context(user_id)
        except Exception as e:
            logger.error(f"Ошибка получения контекста пользователя {user_id}: {e}")
            user_context = {}

        # Нормализуем контекст и context_data, чтобы не пытаться вызывать .get у None или других типов
        if not isinstance(user_context, dict):
            user_context = {}
        if context_data is None or not isinstance(context_data, dict):
            context_data = {}

        # Добавляем контекстные подсказки если есть данные
        if context_data.get('has_pending_actions'):
            text += f"\n\n💡 У вас есть ожидающие действия! Проверьте меню."
        if context_data.get('new_achievements'):
            text += f"\n\n🏆 Получено новое достижение: {context_data['new_achievements']}"

        # Добавляем умные подсказки из контекста
        if user_context.get('smart_tips'):
            tips_to_show = user_context['smart_tips'][:2]
            if tips_to_show:
                text += "\n\n🌟 " + "\n🌟 ".join(tips_to_show)

        # Добавляем приоритетные уведомления
        if user_context.get('priority_level') == 'urgent':
            text = f"🚨 СРОЧНО! {text}"
        elif user_context.get('priority_level') == 'high':
            text = f"🔔 ВАЖНО! {text}"
    
    try:
        return await reply_with_menu(update, text, menu_type, parse_mode, user_id, context_data)
    except TypeError:
        # backward-compat: older reply_with_menu signatures might differ
        return await reply_with_menu(update, text, menu_type, parse_mode, context_data)
    except Exception as e:
        logger.error(f"Ошибка отправки умных уведомлений: {e}")
        # fallback to simple reply
        try:
            return await reply_with_menu(update, text, menu_type, parse_mode)
        except Exception:
            return None


async def notify_about_pending_actions(update, pending_data=None):
    """Отправляет уведомление о ожидающих действиях с контекстными рекомендациями"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if pending_data is None:
        # Получаем актуальные данные об уведомлениях
        from bots.menu_manager import MenuManager
        counts = await MenuManager.get_notification_counts(user_id)
        pending_data = counts
    
    # Получаем контекст для рекомендаций
    user_context = await context_service.get_user_context(user_id) if user_id else None
    
    if pending_data.get('total', 0) > 0:
        # Формируем рекомендации на основе контекста
        recommendations = ""
        if user_context and user_context.get('quick_actions'):
            quick_actions = user_context['quick_actions'][:2]
            if quick_actions:
                recommendations = f"\n\n🎯 Рекомендуем: {', '.join(quick_actions)}"
        
        notification_text = f"""
🔔 *У вас ожидающие действия!*

• 🤝 Встреч: {pending_data.get('meetings', 0)}
• 📅 Активностей сегодня: {pending_data.get('today_activities', 0)}
• 🚨 Срочных: {pending_data.get('urgent_actions', 0)}
• 🔔 Уведомлений: {pending_data.get('notifications', 0)}
{recommendations}

💡 Используйте соответствующие разделы меню для управления.
"""
        return await reply_with_smart_notifications(update, notification_text, 'main', 'Markdown', user_id)
    
    return None


async def send_urgent_notification(update, title, message, urgency='normal'):
    """Отправляет срочное уведомление с соответствующим оформлением"""
    user_id = getattr(update.effective_user, 'id', None)
    
    urgency_icons = {
        'low': 'ℹ️',
        'normal': '🔔', 
        'high': '⚠️',
        'urgent': '🚨'
    }
    
    icon = urgency_icons.get(urgency, '🔔')
    
    # Получаем контекст для персонализированных рекомендаций
    user_context = await context_service.get_user_context(user_id) if user_id else None
    context_tip = ""
    
    if user_context and user_context.get('smart_tips'):
        relevant_tips = [tip for tip in user_context['smart_tips'] if any(word in tip.lower() for word in ['срочн', 'действ', 'подтверд'])]
        if relevant_tips:
            context_tip = f"\n\n💡 {relevant_tips[0]}"
    
    notification_text = f"""
{icon} *{title}*

{message}
{context_tip}

💡 Используйте меню для управления уведомлениями.
"""
    
    return await reply_with_smart_notifications(update, notification_text, 'main', 'Markdown', user_id)


async def send_contextual_welcome(update, additional_message=None):
    """Отправляет персонализированное приветственное сообщение с учетом контекста"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if not user_id:
        # Fallback для случая когда user_id недоступен
        welcome_text = """
👋 Добро пожаловать в ConnectBot!

🤖 Я ваш помощник для корпоративных активностей.

💡 Используйте кнопки ниже для навигации.
"""
        return await reply_with_menu(update, welcome_text, 'main')
    
    # Получаем контекстное приветствие
    contextual_welcome = await context_service.get_contextual_welcome(user_id)
    
    # Получаем детальный контекст для дополнительной информации
    user_context = await context_service.get_user_context(user_id)
    
    # Формируем полное приветственное сообщение
    welcome_parts = [f"👋 {contextual_welcome}"]
    
    # Добавляем дополнительное сообщение если есть
    if additional_message:
        welcome_parts.append(f"\n{additional_message}")
    
    # Добавляем рекомендации по быстрым действиям
    if user_context.get('quick_actions'):
        quick_actions = user_context['quick_actions'][:3]
        if quick_actions:
            welcome_parts.append(f"\n🎯 Быстрые действия: {', '.join(quick_actions)}")
    
    # Добавляем образовательные подсказки для новых пользователей
    if user_context.get('activity_profile', {}).get('experience_level') in ['new', 'beginner']:
        welcome_parts.append("\n💡 Совет: Начните с раздела '🎯 Мои интересы' чтобы настроить предпочтения!")
    
    welcome_text = "\n".join(welcome_parts)
    
    return await reply_with_smart_notifications(update, welcome_text, 'main', None, user_id)


async def send_adaptive_suggestions(update, current_action=None):
    """Отправляет адаптивные предложения на основе текущего контекста пользователя"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if not user_id:
        return None
    
    # Получаем адаптивные предложения
    suggestions = await context_service.get_adaptive_menu_suggestions(user_id)
    
    if not suggestions.get('recommended_actions'):
        return None
    
    # Формируем сообщение с предложениями
    suggestion_text = "💡 *Персональные рекомендации:*\n\n"
    
    # Добавляем рекомендуемые действия
    if suggestions['recommended_actions']:
        suggestion_text += "🎯 *Что сделать:*\n"
        for action in suggestions['recommended_actions'][:3]:
            suggestion_text += f"• {action}\n"
    
    # Добавляем образовательные подсказки
    if suggestions['educational_tips']:
        suggestion_text += "\n🌟 *Советы:*\n"
        for tip in suggestions['educational_tips'][:2]:
            suggestion_text += f"• {tip}\n"
    
    # Подсвечиваем рекомендуемый раздел
    if suggestions['highlight_section']:
        section_names = {
            'profile': '👤 Мой профиль',
            'interests': '🎯 Мои интересы', 
            'calendar': '📅 Календарь',
            'coffee': '☕ Тайный кофе'
        }
        highlighted = section_names.get(suggestions['highlight_section'])
        if highlighted:
            suggestion_text += f"\n📌 *Рекомендуем:* {highlighted}"
    
    return await reply_with_smart_notifications(update, suggestion_text, 'main', 'Markdown', user_id)


async def log_user_interaction(update, action_type, menu_item, success=True):
    """Логирует взаимодействие пользователя для улучшения контекста"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if user_id:
        await context_service.log_user_interaction(user_id, action_type, menu_item, success)
        
        # Очищаем кэш уведомлений при значимых действиях
        if action_type in ['completed_task', 'confirmed_meeting', 'joined_activity']:
            await notification_service.clear_notification_cache(user_id)
            logger.info(f"Кэш уведомлений очищен после действия пользователя {user_id}: {action_type}")


async def send_educational_tip(update, tip_type=None):
    """Отправляет образовательную подсказку пользователю"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if not user_id:
        return None
    
    user_context = await context_service.get_user_context(user_id)
    experience_level = user_context.get('activity_profile', {}).get('experience_level', 'beginner')
    
    # Подсказки в зависимости от уровня опыта
    tips_by_level = {
        'new': [
            "💡 Числа в скобках показывают количество ожидающих действий",
            "🎯 Начните с настройки интересов в разделе '🎯 Мои интересы'",
            "🤝 Тайный кофе - отличный способ познакомиться с коллегами!"
        ],
        'beginner': [
            "🌟 Участвуйте в разных активностях для получения достижений",
            "📅 Регулярно проверяйте календарь чтобы не пропустить события",
            "🔔 Используйте /refresh для обновления счетчиков уведомлений"
        ],
        'intermediate': [
            "🏆 Стремитесь к получению всех достижений для полного профиля",
            "💬 Активно общайтесь с партнерами в Тайном кофе",
            "📊 Анализируйте статистику для улучшения участия"
        ],
        'advanced': [
            "🚀 Вы - эксперт! Помогайте новичкам ориентироваться в системе",
            "🎪 Пробуйте новые форматы встреч и активностей",
            "💫 Делитесь обратной связью для улучшения бота"
        ],
        'expert': [
            "👑 Вы - мастер активностей! Продолжайте вдохновлять коллег!",
            "🌟 Рассмотрите возможность стать ментором для новичков",
            "💡 Предлагайте идеи для новых функций бота"
        ]
    }
    
    # Выбираем подсказку
    tips = tips_by_level.get(experience_level, tips_by_level['beginner'])
    
    if tip_type == 'random':
        import random
        tip = random.choice(tips)
    else:
        tip = tips[0]
    
    tip_text = f"""
🎓 *Образовательная минутка*

{tip}

💡 Уровень: {experience_level.title()}
"""
    
    return await reply_with_smart_notifications(update, tip_text, 'main', 'Markdown', user_id)


async def handle_quick_action(update, action_type, context_data=None):
    """Обрабатывает быстрые действия с учетом контекста"""
    user_id = getattr(update.effective_user, 'id', None)
    
    if not user_id:
        return await reply_with_menu(update, "❌ Не удалось определить пользователя", 'main')
    
    # Логируем действие
    await log_user_interaction(update, 'quick_action', action_type, True)
    
    # Обрабатываем разные типы быстрых действий
    action_handlers = {
        'confirm_urgent': lambda: _handle_confirm_urgent(update, user_id),
        'plan_week': lambda: _handle_plan_week(update, user_id),
        'review_stats': lambda: _handle_review_stats(update, user_id),
        'setup_interests': lambda: _handle_setup_interests(update, user_id)
    }
    
    handler = action_handlers.get(action_type)
    if handler:
        return await handler()
    
    # Fallback
    return await reply_with_menu(update, "✅ Быстрое действие выполнено!", 'main')


async def _handle_confirm_urgent(update, user_id):
    """Обрабатывает подтверждение срочных действий"""
    counts = await notification_service.get_user_notification_counts(user_id)
    
    if counts['urgent_actions'] > 0:
        text = f"✅ Подтверждено {counts['urgent_actions']} срочных действий!"
        # Здесь будет реальная логика подтверждения
    else:
        text = "🎉 Срочных действий нет!"
    
    return await reply_with_smart_notifications(update, text, 'main', None, user_id)


async def _handle_plan_week(update, user_id):
    """Обрабатывает планирование недели"""
    text = """
📋 *Планирование недели*

Рекомендуемые действия на неделю:
• 🗓️ Запланируйте участие в 2-3 активностях
• 🤝 Настройте доступность для Тайного кофе
• 🎯 Проверьте и обновите интересы

💡 Используйте соответствующие разделы меню!
"""
    return await reply_with_smart_notifications(update, text, 'main', 'Markdown', user_id)


async def _handle_review_stats(update, user_id):
    """Обрабатывает просмотр статистики"""
    user_context = await context_service.get_user_context(user_id)
    activity_profile = user_context.get('activity_profile', {})
    
    text = f"""
📊 *Ваша статистика*

• Уровень активности: {activity_profile.get('activity_label', 'Новичок')}
• Всего активностей: {activity_profile.get('total_activities', 0)}
• Участий в встречах: {activity_profile.get('total_meetings', 0)}
• Активность за месяц: {activity_profile.get('recent_activities', 0)}

🎯 Продолжайте участвовать для роста статистики!
"""
    return await reply_with_smart_notifications(update, text, 'profile', 'Markdown', user_id)


async def _handle_setup_interests(update, user_id):
    """Обрабатывает настройку интересов"""
    from employees.models import Employee
    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
        interests_text = await MenuManager.create_interests_menu(employee)
        return await reply_with_smart_notifications(update, interests_text, 'interests', 'Markdown', user_id)
    except Exception as e:
        logger.error(f"Ошибка настройки интересов: {e}")
        return await reply_with_menu(update, "❌ Ошибка загрузки интересов", 'main')