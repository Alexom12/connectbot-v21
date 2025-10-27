"""
Обработчики уведомлений
"""
import logging
from telegram.ext import Application
from bots.utils.message_utils import reply_with_menu
from bots.menu_manager import MenuManager

logger = logging.getLogger(__name__)

async def send_telegram_message(telegram_id, message):
    """Заглушка для отправки Telegram сообщений во время тестирования"""
    logger.info(f"Отправка сообщения пользователю. Длина сообщения: {len(message)}")
    # logger.debug(f"  {message[:70]}...")
    return True

async def send_notification_with_menu(update, message, menu_type='main', parse_mode=None):
    """Отправляет уведомление с соответствующей клавиатурой меню"""
    try:
        await reply_with_menu(update, message, menu_type=menu_type, parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления с меню: {e}")
        return False

async def send_coffee_match_notification(update, match_info):
    """Отправляет уведомление о найденной паре для Тайного кофе"""
    try:
        notification_text = f"""
☕ *НАЙДЕНА ПАРА ДЛЯ ТАЙНОГО КОФЕ!*

🎯 Ваш партнер найден! 
📋 Ваш код: `{match_info.get('employee_code', 'N/A')}`
🎪 Опознавательный знак: *{match_info.get('recognition_sign', 'N/A')}*

💬 Используйте кнопку «💬 Написать сообщение» чтобы начать общение
📅 Используйте «📅 Предложить встречу» чтобы согласовать время

🤫 Помните: сохраняйте анонимность до встречи!
"""
        
        await send_notification_with_menu(
            update, 
            notification_text, 
            menu_type='coffee', 
            parse_mode='Markdown'
        )
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о паре: {e}")
        return False

async def send_activity_reminder(update, activity_info):
    """Отправляет напоминание о предстоящей активности"""
    try:
        activity_name = activity_info.get('name', 'Активность')
        scheduled_time = activity_info.get('time', 'не указано')
        location = activity_info.get('location', 'не указано')
        
        reminder_text = f"""
🔔 *НАПОМИНАНИЕ О АКТИВНОСТИ*

🎯 *{activity_name}*
🕐 Время: {scheduled_time}
📍 Место: {location}

💡 Не забудьте подтвердить участие через меню «📅 Календарь»
"""
        
        await send_notification_with_menu(
            update,
            reminder_text,
            menu_type='calendar',
            parse_mode='Markdown'
        )
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")
        return False

async def send_achievement_notification(update, achievement_info):
    """Отправляет уведомление о получении достижения"""
    try:
        achievement_name = achievement_info.get('name', 'Достижение')
        achievement_icon = achievement_info.get('icon', '🏆')
        description = achievement_info.get('description', '')
        
        achievement_text = f"""
🏆 *НОВОЕ ДОСТИЖЕНИЕ!*

{achievement_icon} *{achievement_name}*

{description}

🎉 Поздравляем с получением достижения! 
Продолжайте в том же духе! 🚀
"""
        
        await send_notification_with_menu(
            update,
            achievement_text,
            menu_type='main',
            parse_mode='Markdown'
        )
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о достижении: {e}")
        return False

async def send_system_notification(update, notification_data):
    """Отправляет системное уведомление"""
    try:
        title = notification_data.get('title', 'Системное уведомление')
        message = notification_data.get('message', '')
        notification_type = notification_data.get('type', 'info')
        
        # Иконки для разных типов уведомлений
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        
        icon = icons.get(notification_type, 'ℹ️')
        
        system_text = f"""
{icon} *{title}*

{message}

💡 Для управления уведомлениями используйте меню «⚙️ Настройки»
"""
        
        await send_notification_with_menu(
            update,
            system_text,
            menu_type='main',
            parse_mode='Markdown'
        )
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки системного уведомления: {e}")
        return False

async def send_preferences_update_notification(update, update_info):
    """Отправляет уведомление об обновлении предпочтений"""
    try:
        update_type = update_info.get('type', 'настройки')
        changes = update_info.get('changes', 'изменения')
        
        preferences_text = f"""
⚙️ *ОБНОВЛЕНИЕ НАСТРОЕК*

✅ Ваши {update_type} успешно обновлены!

{changes}

💡 Вы можете проверить изменения в меню «🎯 Мои интересы»
"""
        
        await send_notification_with_menu(
            update,
            preferences_text,
            menu_type='interests',
            parse_mode='Markdown'
        )
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о настройках: {e}")
        return False

async def handle_notification_command(update, context):
    """Обработчик команды для тестирования уведомлений"""
    try:
        test_notification = {
            'title': 'Тестовое уведомление',
            'message': 'Это тестовое уведомление для проверки работы системы.',
            'type': 'info'
        }
        
        await send_system_notification(update, test_notification)
        
    except Exception as e:
        logger.error(f"Ошибка тестирования уведомлений: {e}")
        await send_notification_with_menu(
            update,
            "❌ Ошибка отправки тестового уведомления",
            menu_type='main'
        )

def setup_notification_handlers(application: Application):
    """Настройка обработчиков уведомлений"""
    try:
        from telegram.ext import CommandHandler
        
        # Добавляем тестовую команду для уведомлений
        application.add_handler(CommandHandler("test_notification", handle_notification_command))
        
        logger.info("Обработчики уведомлений настроены")
        
    except Exception as e:
        logger.error(f"Ошибка настройки обработчиков уведомлений: {e}")