"""
Менеджер меню для ConnectBot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)


class MenuManager:
    """Управление меню и навигацией бота"""
    
    @staticmethod
    async def create_main_menu():
        """Главное меню"""
        keyboard = [
            [InlineKeyboardButton("Мой профиль", callback_data="menu_profile")],
            [InlineKeyboardButton("Мои интересы", callback_data="menu_interests")],
            [InlineKeyboardButton("Календарь активностей", callback_data="menu_calendar")],
            [InlineKeyboardButton("📝 Оставить отзыв", callback_data="feedback_start")],
            [InlineKeyboardButton("Достижения", callback_data="menu_achievements")],
            [InlineKeyboardButton("Помощь", callback_data="menu_help")],
            [InlineKeyboardButton("Настройки", callback_data="menu_settings")],
        ]
        
        return {
            'text': "*ConnectBot - Главное меню*\n\nВыберите раздел:",
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_profile_menu(employee):
        """Меню профиля сотрудника"""
        from employees.utils import PreferenceManager
        
        try:
            # Получаем статистику
            interests = await PreferenceManager.get_employee_interests(employee)
            active_interests = [ei for ei in interests if ei.is_active]
            
            # Безопасно получаем данные отдела
            department_name = 'Не указан'
            try:
                if employee.department:
                    department_name = employee.department.name
            except:
                department_name = 'Не указан'
            
            # Безопасно получаем данные бизнес-центра
            bc_name = 'Не указан'
            try:
                if employee.business_center:
                    bc_name = employee.business_center.name
            except:
                bc_name = 'Не указан'
            
            # Безопасно получаем дату создания
            created_date = 'Не указана'
            try:
                if employee.created_at:
                    created_date = employee.created_at.strftime('%d.%m.%Y')
            except:
                created_date = 'Не указана'
            
            profile_text = f"""
*Профиль: {employee.full_name}*

*Основная информация:*
• Должность: {employee.position or 'Не указана'}
• Отдел: {department_name}
• БЦ: {bc_name}

*Статистика:*
• Активных интересов: {len(active_interests)}
• В системе с: {created_date}
• Авторизован: {'Да' if employee.authorized else 'Нет'}
"""
            keyboard = [
                [InlineKeyboardButton("Подробная статистика", callback_data="profile_stats")],
                [InlineKeyboardButton("Мои достижения", callback_data="profile_achievements")],
                [InlineKeyboardButton("Активность по месяцам", callback_data="profile_activity")],
                [InlineKeyboardButton("Назад в меню", callback_data="back_main")],
            ]
            
            return {
                'text': profile_text,
                'reply_markup': InlineKeyboardMarkup(keyboard),
                'parse_mode': 'Markdown'
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания меню профиля: {e}")
            # Возвращаем упрощенное меню при ошибке
            simple_text = f"""
*Профиль: {getattr(employee, 'full_name', 'Неизвестно')}*

Извините, произошла ошибка при загрузке данных профиля.
Попробуйте позже или обратитесь к администратору.
"""
            keyboard = [
                [InlineKeyboardButton("Назад в меню", callback_data="back_main")],
            ]
            
            return {
                'text': simple_text,
                'reply_markup': InlineKeyboardMarkup(keyboard),
                'parse_mode': 'Markdown'
            }
    
    @staticmethod
    async def create_interests_menu(employee):
        """Меню управления интересами"""
        from employees.utils import PreferenceManager
        
        all_interests = await PreferenceManager.get_all_interests()
        employee_interests = await PreferenceManager.get_employee_interests(employee)
        
        # Создаем словарь активных интересов
        active_interests = {ei.interest.code: ei for ei in employee_interests if ei.is_active}
        
        keyboard = []
        for interest in all_interests:
            is_active = interest.code in active_interests
            status_icon = "✅" if is_active else "❌"
            callback_data = f"toggle_interest_{interest.code}"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_icon} {interest.emoji} {interest.name}",
                    callback_data=callback_data
                )
            ])
        
        # Кнопки действий
        action_buttons = [
            [InlineKeyboardButton("💾 Сохранить изменения", callback_data="save_interests")],
            [InlineKeyboardButton("🚫 Отписаться от всего", callback_data="disable_all_interests")],
            [InlineKeyboardButton("↩️ Назад в меню", callback_data="back_main")],
        ]
        
        keyboard.extend(action_buttons)
        
        active_count = len(active_interests)
        menu_text = f"""
🎯 *Управление интересами*

Активных подписок: {active_count}/{len(all_interests)}

Выберите активности, уведомления о которых хотите получать:
• ✅ - подписан
• ❌ - не подписан

*Не забудьте нажать «💾 Сохранить изменения»!*
"""
        
        return {
            'text': menu_text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_calendar_menu(employee):
        """Меню календаря активностей"""
        # Заглушка - в реальности здесь будет запрос к БД
        calendar_text = """
📅 *Ваши активности на этой неделе*

*Понедельник:*
• 15:00 ☕️ Тайный кофе с коллегой

*Среда:*
• 13:00 🍝 Обед вслепую
• 18:00 ♟️ Шахматный турнир

*Пятница:*
• 17:00 🎲 Вечер настольных игр

Используйте кнопки ниже для управления участием.
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить участие", callback_data="confirm_participation")],
            [InlineKeyboardButton("⏭️ Отказаться от встречи", callback_data="decline_activity")],
            [InlineKeyboardButton("🔄 Обновить календарь", callback_data="refresh_calendar")],
            [InlineKeyboardButton("↩️ Назад в меню", callback_data="back_main")],
        ]
        
        return {
            'text': calendar_text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_achievements_menu(employee):
        """Меню достижений"""
        achievements_text = """
🏆 *Ваши достижения*

*Получено: 3/8*

✅ 🎯 *Первая встреча*
   Принять участие в первой активности

✅ 🦋 *Социальная бабочка* 
   Поучаствовать в 3 разных активностях

✅ ☕️ *Кофеман*
   Принять участие в 3 Тайных кофе

🔒 ♟️ *Шахматный гроссмейстер*
   Сыграть 10 партий в шахматы (3/10)

🔒 🏓 *Чемпион по теннису*
   Сыграть 15 партий в настольный теннис (0/15)

*Продолжайте в том же духе!* 🚀
"""
        
        keyboard = [
            [InlineKeyboardButton("📈 Прогресс по достижениям", callback_data="achievements_progress")],
            [InlineKeyboardButton("🏅 Топ сотрудников", callback_data="achievements_leaderboard")],
            [InlineKeyboardButton("↩️ Назад в меню", callback_data="back_main")],
        ]
        
        return {
            'text': achievements_text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_help_menu():
        """Меню помощи"""
        help_text = """
🆘 *Центр помощи ConnectBot*

*Основные команды:*
/start - Начать работу с ботом
/menu - Главное меню  
/preferences - Настройка интересов
/help - Показать эту справку

*Частые вопросы:*
"""
        
        keyboard = [
            [InlineKeyboardButton("❓ Как изменить интересы?", callback_data="help_interests")],
            [InlineKeyboardButton("❓ Как отказаться от активности?", callback_data="help_optout")],
            [InlineKeyboardButton("❓ Не приходят уведомления", callback_data="help_notifications")],
            [InlineKeyboardButton("📞 Связаться с администратором", callback_data="help_contact_admin")],
            [InlineKeyboardButton("↩️ Назад в меню", callback_data="back_main")],
        ]
        
        return {
            'text': help_text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_settings_menu():
        """Меню настроек"""
        settings_text = """
⚙️ *Настройки*

Здесь вы можете настроить работу бота под себя:

• 🔔 Уведомления - настройка частоты оповещений
• 👤 Данные профиля - просмотр и редактирование
• 🌐 Язык - выбор языка интерфейса
• 📱 Оформление - темы и внешний вид

*Выберите раздел для настройки:*
"""
        
        keyboard = [
            [InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton("👤 Данные профиля", callback_data="settings_profile")],
            [InlineKeyboardButton("🌐 Язык", callback_data="settings_language")],
            [InlineKeyboardButton("📱 Оформление", callback_data="settings_theme")],
            [InlineKeyboardButton("↩️ Назад в меню", callback_data="back_main")],
        ]
        
        return {
            'text': settings_text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': 'Markdown'
        }
    
    @staticmethod
    async def create_back_button(target_menu="main"):
        """Создает кнопку Назад"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=f"back_{target_menu}")]
        ])

    # Backwards-compatible aliases for older callers that expect get_* naming
    @staticmethod
    async def get_main_menu(*args, **kwargs):
        return await MenuManager.create_main_menu()

    @staticmethod
    async def get_profile_menu(employee, *args, **kwargs):
        return await MenuManager.create_profile_menu(employee)

    @staticmethod
    async def get_interests_menu(employee, *args, **kwargs):
        return await MenuManager.create_interests_menu(employee)

    @staticmethod
    async def get_calendar_menu(employee, *args, **kwargs):
        return await MenuManager.create_calendar_menu(employee)

    @staticmethod
    async def get_achievements_menu(employee, *args, **kwargs):
        return await MenuManager.create_achievements_menu(employee)

    @staticmethod
    async def get_help_menu(*args, **kwargs):
        return await MenuManager.create_help_menu()

    @staticmethod
    async def get_settings_menu(*args, **kwargs):
        return await MenuManager.create_settings_menu()

    @staticmethod
    async def get_back_button(target_menu="main", *args, **kwargs):
        return await MenuManager.create_back_button(target_menu)