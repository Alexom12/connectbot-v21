from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bots.services.redis_service import redis_service
import logging
from employees.utils import PreferenceManager
from employees.models import Employee
from bots.menu_manager import MenuManager
from asgiref.sync import sync_to_async
from bots.utils.message_utils import reply_with_menu

logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню с активностями"""
    menu_text = await MenuManager.create_main_menu_message()
    await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')

async def handle_activity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора активности (для обратной совместимости)"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer activity selection callback: {e}")
    
    user_id = query.from_user.id
    activity_type = query.data.replace('activity_', '')
    
    # Сохраняем выбранную активность в контексте
    context.user_data['selected_activity'] = activity_type
    
    # Показываем соответствующее меню через Reply клавиатуру
    activity_names = {
        'secret_coffee': '☕️ Тайный кофе',
        'chess': '♟️ Шахматы',
        'ping_pong': '🏓 Настольный теннис',
        'photo_quest': '📸 Фотоквесты',
        'workshop': '🧠 Мастер-классы',
    }
    
    activity_name = activity_names.get(activity_type, activity_type)
    
    activity_text = f"""
*{activity_name}*

🤖 *Новая система навигации*

Для управления активностями теперь используйте кнопки внизу экрана:

👤 *Мой профиль* - информация о подписках
🎯 *Мои интересы* - управление активностями
📅 *Календарь* - ваши мероприятия

💡 Все функции теперь доступны через удобное меню!
"""
    
    await reply_with_menu(update, activity_text, menu_type='main', parse_mode='Markdown')

async def handle_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подписки/отписки от активности (для обратной совместимости)"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer subscription callback: {e}")
    
    user_id = query.from_user.id
    data = query.data

    # Универсальная обработка back_<target> — возвращаемся в соответствующее меню
    if data.startswith('back_'):
        target = data.replace('back_', '')
        try:
            if target in ('main', 'to_main', 'back_main'):
                menu_text = await MenuManager.create_main_menu_message()
                await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')
            elif target == 'profile':
                from employees.models import Employee
                employee = await Employee.objects.aget(telegram_id=user_id)
                profile_text = await MenuManager.create_profile_menu(employee)
                await reply_with_menu(update, profile_text, menu_type='profile', parse_mode='Markdown')
            elif target == 'help':
                help_text = await MenuManager.create_help_menu()
                await reply_with_menu(update, help_text, menu_type='help', parse_mode='Markdown')
            elif target == 'settings':
                settings_text = await MenuManager.create_settings_menu()
                await reply_with_menu(update, settings_text, menu_type='settings', parse_mode='Markdown')
            elif target == 'interests':
                from employees.models import Employee
                employee = await Employee.objects.aget(telegram_id=user_id)
                interests_text = await MenuManager.create_interests_menu(employee)
                await reply_with_menu(update, interests_text, menu_type='interests', parse_mode='Markdown')
            else:
                menu_text = await MenuManager.create_main_menu_message()
                await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')
        except Exception:
            logger.exception(f"Ошибка при обработке back callback '{data}'")
            menu_text = await MenuManager.create_main_menu_message()
            await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')
        return
    
    if data.startswith('subscribe_'):
        activity_type = data.replace('subscribe_', '')
        # TODO: Реализовать логику подписки
        subscribed_text = "✅ Вы успешно подписались на активность!"
        await reply_with_menu(update, subscribed_text, menu_type='main', parse_mode='Markdown')
        
    elif data.startswith('unsubscribe_'):
        activity_type = data.replace('unsubscribe_', '')
        # TODO: Реализовать логику отписки
        unsubscribed_text = "❌ Вы отписались от активности."
        await reply_with_menu(update, unsubscribed_text, menu_type='main', parse_mode='Markdown')

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий из главного меню (menu_*) - для обратной совместимости"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer menu callback: {e}")

    user_id = query.from_user.id
    logger.info(f"handle_menu_callback invoked: user={user_id} data={query.data}")

    try:
        employee = await Employee.objects.aget(telegram_id=user_id)
    except Employee.DoesNotExist:
        await query.edit_message_text("⚠️ Сначала завершите регистрацию через /start")
        return

    data = query.data

    # Навигация по основным разделам
    if data == 'menu_profile':
        profile_text = await MenuManager.create_profile_menu(employee)
        await reply_with_menu(update, profile_text, menu_type='profile', parse_mode='Markdown')

    elif data == 'menu_interests':
        interests_text = await MenuManager.create_interests_menu(employee)
        await reply_with_menu(update, interests_text, menu_type='interests', parse_mode='Markdown')

    elif data == 'menu_calendar':
        calendar_text = await MenuManager.create_calendar_menu(employee)
        await reply_with_menu(update, calendar_text, menu_type='calendar', parse_mode='Markdown')

    elif data == 'menu_achievements':
        achievements_text = await MenuManager.create_achievements_menu(employee)
        await reply_with_menu(update, achievements_text, menu_type='main', parse_mode='Markdown')

    elif data == 'menu_help':
        help_text = await MenuManager.create_help_menu()
        await reply_with_menu(update, help_text, menu_type='help', parse_mode='Markdown')

    elif data == 'menu_settings':
        settings_text = await MenuManager.create_settings_menu()
        await reply_with_menu(update, settings_text, menu_type='settings', parse_mode='Markdown')

    elif data == 'back_main' or data == 'back_to_main':
        menu_text = await MenuManager.create_main_menu_message()
        await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')

    # Профиль - дополнительные действия
    elif data.startswith('profile_'):
        action = data.replace('profile_', '')
        logger.info(f"Profile action requested: {action} for user {user_id}")
        if action == 'stats':
            try:
                stats_list = await sync_to_async(list)(employee.get_activity_stats())
                stats_lines = []
                for s in stats_list:
                    activity_label = s.get('activity_type') or s.get('activity_type', 'неизвестно')
                    count = s.get('count', s.get('count', 0))
                    stats_lines.append(f"• {activity_label}: {count}")
                if not stats_lines:
                    stats_lines = ["Нет данных по активностям"]
            except Exception:
                stats_lines = ["Статистика недоступна"]

            try:
                interests = await sync_to_async(employee.get_interests_list)()
                if interests:
                    interests_text = ', '.join([f"{i.emoji} {i.name}" for i in interests])
                else:
                    interests_text = 'Не выбраны'
            except Exception:
                interests_text = 'Не удалось получить интересы'

            text = "📈 *Моя статистика*\n\n"
            text += "Активности:\n"
            text += "\n".join(stats_lines) + "\n\n"
            text += f"Интересы: {interests_text}\n"
            await reply_with_menu(update, text, menu_type='profile', parse_mode='Markdown')
            
        elif action == 'achievements':
            try:
                ach_list = await sync_to_async(list)(employee.achievements.select_related('achievement').all())
                achievements_lines = []
                for ea in ach_list:
                    icon = getattr(ea.achievement, 'icon', '') or ''
                    name = getattr(ea.achievement, 'name', 'Неизвестно')
                    achievements_lines.append(f"✅ {icon} {name}")
                if not achievements_lines:
                    achievements_lines = ["У вас пока нет достижений. Участвуйте в активностях!"]
            except Exception:
                achievements_lines = ["Не удалось получить достижения"]

            text = "🏅 *Мои достижения*\n\n" + "\n".join(achievements_lines)
            await reply_with_menu(update, text, menu_type='main', parse_mode='Markdown')
            
        elif action == 'activity':
            try:
                from django.db.models import Count
                from django.db.models.functions import ExtractYear, ExtractMonth
                import calendar

                qs = employee.activities.annotate(
                    year=ExtractYear('activity__scheduled_date'),
                    month=ExtractMonth('activity__scheduled_date')
                ).values('year', 'month').annotate(count=Count('id')).order_by('-year', '-month')

                monthly = await sync_to_async(list)(qs)

                if monthly:
                    lines = []
                    for r in monthly:
                        y = r.get('year') or ''
                        m = r.get('month') or 0
                        month_name = calendar.month_name[m] if m and m <= 12 else str(m)
                        lines.append(f"• {month_name} {y}: {r.get('count', 0)}")
                else:
                    lines = ["Нет данных по активности за месяцы"]
            except Exception:
                logger.exception("Ошибка получения активности по месяцам для профиля")
                lines = ["Не удалось получить данные по активности"]

            text = "📅 *Активность по месяцам*\n\n" + "\n".join(lines)
            await reply_with_menu(update, text, menu_type='profile', parse_mode='Markdown')
            
        else:
            profile_text = await MenuManager.create_profile_menu(employee)
            await reply_with_menu(update, profile_text, menu_type='profile', parse_mode='Markdown')

    # Достижения
    elif data.startswith('achievements_'):
        action = data.replace('achievements_', '')
        if action == 'progress':
            await reply_with_menu(update, "📈 Прогресс достижений: подробный отчёт скоро будет доступен.", menu_type='main', parse_mode='Markdown')
        elif action == 'leaderboard':
            await reply_with_menu(update, "🏆 Топ сотрудников: функция в разработке.", menu_type='main', parse_mode='Markdown')
        else:
            achievements_text = await MenuManager.create_achievements_menu(employee)
            await reply_with_menu(update, achievements_text, menu_type='main', parse_mode='Markdown')

    # Помощь — тематические страницы
    elif data.startswith('help_'):
        topic = data.replace('help_', '')
        help_topics = {
            'interests': '❓ Как изменить интересы? Откройте Главное меню → Мои интересы и переключайте кнопки.',
            'optout': '❓ Как отказаться от активности? Нажмите «Отписаться» в меню активности или используйте настройку интересов.',
            'notifications': '❓ Не приходят уведомления? Проверьте настройки /preferences и подписки на интересы.',
            'contact_admin': '📞 Связь с администратором: @hr_admin'
        }
        text = help_topics.get(topic, 'Тема помощи не найдена')
        await reply_with_menu(update, text, menu_type='help', parse_mode='Markdown')

    # Настройки
    elif data.startswith('settings_'):
        key = data.replace('settings_', '')
        settings_text = await MenuManager.create_settings_menu()
        await reply_with_menu(update, settings_text, menu_type='settings', parse_mode='Markdown')

    # Календарь: действия
    elif data == 'confirm_participation':
        await reply_with_menu(update, "✅ Вы подтвердили участие. Спасибо!", menu_type='calendar', parse_mode='Markdown')
    elif data == 'decline_activity':
        await reply_with_menu(update, "⏭️ Вы отказались от участия. Сообщение отправлено.", menu_type='calendar', parse_mode='Markdown')
    elif data == 'refresh_calendar':
        calendar_text = await MenuManager.create_calendar_menu(employee)
        await reply_with_menu(update, calendar_text, menu_type='calendar', parse_mode='Markdown')

    else:
        # Неизвестная кнопка — возврат в главное меню
        menu_text = await MenuManager.create_main_menu_message()
        await reply_with_menu(update, menu_text, menu_type='main', parse_mode='Markdown')

def setup_menu_handlers(application):
    """Настройка обработчиков меню (для обратной совместимости)"""
    # Оставляем только базовые обработчики для обратной совместимости
    application.add_handler(CallbackQueryHandler(handle_activity_selection, pattern="^activity_"))
    application.add_handler(CallbackQueryHandler(handle_subscription, pattern="^(subscribe|unsubscribe)_"))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^back_to_main$"))
    
    # Menu navigation (main menu buttons)
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu_"))
    
    # Profile submenu callbacks (profile_...)
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^profile_"))
    
    # Catch any back_* callbacks (back_main, back_help, back_settings, etc.)
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^back_"))
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^back_main$"))