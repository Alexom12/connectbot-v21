"""
Менеджер меню для ConnectBot
"""
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async
import logging
from bots.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class MenuManager:
    """Управление меню и навигацией бота"""
    
    @staticmethod
    async def get_notification_counts(user_id):
        """Получить количество непрочитанных уведомлений и ожидающих действий"""
        try:
            return await notification_service.get_user_notification_counts(user_id)
        except Exception as e:
            logger.error(f"Ошибка получения счетчиков уведомлений через сервис: {e}")
            return {
                'total': 0,
                'today_activities': 0,
                'week_activities': 0,
                'meetings': 0,
                'notifications': 0,
                'urgent_actions': 0
            }
    
    @staticmethod
    async def format_button_with_count(button_text, count, show_zero=False):
        """Форматирует кнопку с счетчиком уведомлений"""
        if count > 0:
            return f"{button_text} ({count})"
        elif show_zero:
            return f"{button_text} (0)"
        return button_text
    
    @staticmethod
    async def create_main_reply_keyboard(user_id=None):
        """Создает основную Reply клавиатуру для главного меню с уведомлениями"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'total': 0, 
            'today_activities': 0, 
            'meetings': 0, 
            'notifications': 0
        }
        
        # Определяем эмодзи для кнопки уведомлений
        notification_emoji = "🔔" if counts['notifications'] > 0 else "❓"
        
        keyboard = [
            [
                KeyboardButton(await MenuManager.format_button_with_count("👤 Мой профиль", counts['total'])),
                KeyboardButton("🎯 Мои интересы")
            ],
            [
                KeyboardButton(await MenuManager.format_button_with_count("📅 Календарь", counts['today_activities'])),
                KeyboardButton("🏅 Достижения")
            ],
            [
                KeyboardButton(await MenuManager.format_button_with_count("☕ Тайный кофе", counts['meetings'])),
                KeyboardButton("⚙️ Настройки")
            ],
            [
                KeyboardButton(await MenuManager.format_button_with_count(f"{notification_emoji} Помощь", counts['notifications']))
            ],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_profile_reply_keyboard(user_id=None):
        """Клавиатура для меню профиля с уведомлениями"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'week_activities': 0, 
            'total': 0
        }
        
        keyboard = [
            [
                KeyboardButton("📊 Статистика"),
                KeyboardButton(await MenuManager.format_button_with_count("🏆 Достижения", counts['week_activities']))
            ],
            [
                KeyboardButton("📈 Активность"),
                KeyboardButton("⬅️ Назад в меню")
            ],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_interests_reply_keyboard(user_id=None):
        """Клавиатура для меню интересов"""
        # Нажатие на интересы теперь переключает их мгновенно через InlineKeyboard.
        # Reply-клавиатура содержит только управляющие действия (без кнопки Сохранить).
        # Убираем кнопку массовой отписки — оставляем только возврат в меню
        keyboard = [
            [KeyboardButton("⬅️ Назад в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_interests_selection_keyboard(employee, pending_codes=None):
        """Клавиатура для выбора интересов с кнопками переключения.

        Принимает optional pending_codes (set of interest.code) — это позволяет визуализировать временные изменения
        перед сохранением.
        Также сохраняет маппинг отображаемой метки -> код интереса в сессии бота (Redis) для обработки нажатий.
        """
        try:
            from employees.utils import PreferenceManager
            from employees.redis_utils import RedisManager

            if pending_codes is None:
                pending_codes = set()

            all_interests = await PreferenceManager.get_all_interests()
            employee_interests = await PreferenceManager.get_employee_interests(employee)

            current_active = {ei.interest.code for ei in employee_interests if ei.is_active}

            # Используем InlineKeyboard: callback_data будет содержать код интереса
            inline_keyboard = []
            row = []

            for interest in all_interests:
                # pending_codes overrides DB state when present
                if interest.code in pending_codes:
                    is_active = True
                elif interest.code in pending_codes and pending_codes is not None:
                    is_active = True
                else:
                    is_active = interest.code in current_active

                button_text = f"{('✅' if is_active else '❌')} {interest.emoji} {interest.name}"
                callback = f"toggle_interest_{interest.code}"
                row.append(InlineKeyboardButton(button_text, callback_data=callback))

                # Формируем ряды по 2 кнопки
                if len(row) == 2:
                    inline_keyboard.append(row)
                    row = []

            if row:
                inline_keyboard.append(row)

            # Раньше здесь были action-кнопки (сохранить/отписаться/назад).
            # Теперь мы возвращаем только кнопки интересов как InlineKeyboard.

            try:
                # логируем для диагностики
                total_buttons = sum(len(r) for r in inline_keyboard)
                logger.info(f"INTERESTS_DEBUG: Created InlineKeyboard for user {getattr(employee, 'telegram_id', getattr(employee, 'telegram_id', 'unknown'))}, buttons={total_buttons}")
            except Exception:
                pass

            return InlineKeyboardMarkup(inline_keyboard)

        except Exception as e:
            logger.error(f"Ошибка создания клавиатуры выбора интересов: {e}")
            return await MenuManager.create_interests_reply_keyboard()
    
    @staticmethod
    async def create_calendar_reply_keyboard(user_id=None):
        """Клавиатура для календаря с уведомлениями"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'today_activities': 0, 
            'urgent_actions': 0
        }
        
        confirm_button_text = "✅ Подтвердить"
        if counts['urgent_actions'] > 0:
            confirm_button_text = f"🚨 Подтвердить ({counts['urgent_actions']})"
        elif counts['today_activities'] > 0:
            confirm_button_text = await MenuManager.format_button_with_count("✅ Подтвердить", counts['today_activities'])
        
        keyboard = [
            [
                KeyboardButton(confirm_button_text),
                KeyboardButton("⏭️ Отказаться")
            ],
            [
                KeyboardButton("🔄 Обновить"),
                KeyboardButton("⬅️ Назад в меню")
            ],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_settings_reply_keyboard(user_id=None):
        """Клавиатура для настроек"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'notifications': 0
        }
        
        keyboard = [
            [
                KeyboardButton(await MenuManager.format_button_with_count("🔔 Уведомления", counts['notifications'])),
                KeyboardButton("👤 Данные профиля")
            ],
            [
                KeyboardButton("🌐 Язык"),
                KeyboardButton("📱 Оформление")
            ],
            [
                KeyboardButton("⬅️ Назад в меню")
            ],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_help_reply_keyboard(user_id=None):
        """Клавиатура для помощи"""
        keyboard = [
            [KeyboardButton("❓ Как изменить интересы"), KeyboardButton("❓ Не приходят уведомления")],
            [KeyboardButton("📞 Связаться с админом"), KeyboardButton("⬅️ Назад в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    async def create_coffee_reply_keyboard(user_id=None):
        """Клавиатура для Тайного кофе с уведомлениями"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'meetings': 0
        }
        
        keyboard = [
            [
                KeyboardButton("💬 Написать сообщение"),
                KeyboardButton(await MenuManager.format_button_with_count("📅 Предложить встречу", counts['meetings']))
            ],
            [
                KeyboardButton("📋 Инструкция"),
                KeyboardButton("⬅️ Назад в меню")
            ],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    async def get_reply_keyboard_for_menu(menu_type, user_id=None, employee=None):
        """Возвращает соответствующую Reply клавиатуру для типа меню с уведомлениями"""
        keyboards = {
            'main': lambda: MenuManager.create_main_reply_keyboard(user_id),
            'profile': lambda: MenuManager.create_profile_reply_keyboard(user_id),
            'interests': lambda: MenuManager.create_interests_reply_keyboard(user_id),
            'interests_selection': lambda: MenuManager.create_interests_selection_keyboard(employee),
            'calendar': lambda: MenuManager.create_calendar_reply_keyboard(user_id),
            'settings': lambda: MenuManager.create_settings_reply_keyboard(user_id),
            'help': lambda: MenuManager.create_help_reply_keyboard(user_id),
            'coffee': lambda: MenuManager.create_coffee_reply_keyboard(user_id),
        }
        
        # Специальная логика для interests: если есть employee — показываем Reply-клавиатуру
        # с управляющими кнопками (Unsubscribe, Back). Inline-кнопки с самими интересами
        # генерируются и отправляются отдельно (чтобы в одном сообщении были и Inline, и Reply).
        if menu_type == 'interests':
            # Если employee не передан, пробуем найти по user_id
            if not employee and user_id:
                try:
                    from employees.models import Employee
                    employee = await Employee.objects.aget(telegram_id=user_id)
                except Exception:
                    employee = None

            # Всегда возвращаем Reply-клавиатуру для управления (без Inline)
            return await MenuManager.create_interests_reply_keyboard(user_id)

        creator = keyboards.get(menu_type)
        if creator:
            return await creator()
        else:
            return await MenuManager.create_main_reply_keyboard(user_id)

    @staticmethod
    async def create_main_menu_message(user_id=None):
        """Текст главного меню с информацией об уведомлениях"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {
            'total': 0, 
            'meetings': 0, 
            'today_activities': 0, 
            'notifications': 0, 
            'urgent_actions': 0
        }
        
        notification_info = ""
        if counts['total'] > 0:
            urgent_section = ""
            if counts['urgent_actions'] > 0:
                urgent_section = f"🚨 *Срочные действия: {counts['urgent_actions']}*\n"
            
            notification_info = f"""
🔔 *У вас {counts['total']} ожидающих действий:*

{urgent_section}• 🤝 Встреч: {counts['meetings']}
• 📅 Активностей сегодня: {counts['today_activities']}
• 🔔 Уведомлений: {counts['notifications']}
"""
        else:
            notification_info = "🎉 *Все действия завершены! Отличная работа!*"

        return f"""
*ConnectBot - Главное меню*

{notification_info}

Выберите раздел:

👤 *Мой профиль* - информация и статистика
🎯 *Мои интересы* - управление подписками  
📅 *Календарь* - ваши активности
🏅 *Достижения* - ваши награды
☕ *Тайный кофе* - анонимные встречи
⚙️ *Настройки* - настройки бота
❓ *Помощь* - справка и поддержка

💡 Используйте /refresh для обновления счетчиков
"""

    @staticmethod
    async def create_profile_menu(employee):
        """Меню профиля сотрудника с уведомлениями"""
        try:
            # Используем sync_to_async для Django ORM операций
            from employees.utils import PreferenceManager
            
            interests = await PreferenceManager.get_employee_interests(employee)
            active_interests = [ei for ei in interests if ei.is_active]
            
            # Получаем счетчики для пользователя
            counts = await MenuManager.get_notification_counts(employee.telegram_id)
            
            # Безопасно получаем данные с помощью sync_to_async
            @sync_to_async
            def get_department_name():
                return getattr(employee.department, 'name', 'Не указан') if employee.department else 'Не указан'
            
            @sync_to_async
            def get_bc_name():
                return getattr(employee.business_center, 'name', 'Не указан') if employee.business_center else 'Не указан'
            
            @sync_to_async
            def get_created_date():
                return employee.created_at.strftime('%d.%m.%Y') if employee.created_at else 'Не указана'
            
            department_name = await get_department_name()
            bc_name = await get_bc_name()
            created_date = await get_created_date()
            
            # Создаем бейдж уведомлений
            notification_badge = ""
            if counts['total'] > 0:
                if counts['urgent_actions'] > 0:
                    notification_badge = f" 🚨 ({counts['urgent_actions']} срочных)"
                else:
                    notification_badge = f" 🔔 ({counts['total']})"
            
            profile_text = f"""
*Профиль: {employee.full_name}{notification_badge}*

*Основная информация:*
• Должность: {employee.position or 'Не указана'}
• Отдел: {department_name}
• БЦ: {bc_name}

*Статистика:*
• Активных интересов: {len(active_interests)}
• В системе с: {created_date}
• Авторизован: {'Да' if employee.authorized else 'Нет'}

*Текущие уведомления:*
• 🤝 Ожидающие встречи: {counts['meetings']}
• 📅 Активностей сегодня: {counts['today_activities']}
• 🚨 Срочные действия: {counts['urgent_actions']}
• 🔔 Всего уведомлений: {counts['total']}

Используйте кнопки ниже для просмотра детальной статистики.
"""
            
            return profile_text
            
        except Exception as e:
            logger.error(f"Ошибка создания меню профиля: {e}")
            return f"*Профиль: {getattr(employee, 'full_name', 'Неизвестно')}*\n\nОшибка загрузки данных. Попробуйте позже."

    @staticmethod
    async def create_interests_menu(employee, selection_mode=False):
        """Меню управления интересами"""
        try:
            from employees.utils import PreferenceManager

            all_interests = await PreferenceManager.get_all_interests()
            employee_interests = await PreferenceManager.get_employee_interests(employee)

            active_interests = {ei.interest.code: ei for ei in employee_interests if ei.is_active}
            active_count = len(active_interests)

            interests_list = ""
            for interest in all_interests:
                is_active = interest.code in active_interests
                status_icon = "✅" if is_active else "❌"
                interests_list += f"{status_icon} {interest.emoji} {interest.name}\n"

            # Получаем счетчики для контекста
            counts = await MenuManager.get_notification_counts(employee.telegram_id)

            notification_context = ""
            if counts['today_activities'] > 0:
                notification_context = f"\n💡 У вас {counts['today_activities']} активностей сегодня!"

            if selection_mode:
                menu_text = f"""
🎯 *Управление интересами - Режим выбора*

Активных подписок: {active_count}/{len(all_interests)}
{notification_context}

*Нажмите на интерес для переключения:*

{interests_list}

*Инструкция:*
Нажмите на интерес для включения/выключения
"""
            else:
                menu_text = f"""
🎯 *Управление интересами*

Активных подписок: {active_count}/{len(all_interests)}
{notification_context}

*Ваши интересы:*
{interests_list}

*Инструкция:*
Нажмите «💾 Сохранить» чтобы применить изменения
"""

            return menu_text

        except Exception as e:
            logger.error(f"Ошибка создания меню интересов: {e}")
            return "❌ Ошибка загрузки интересов. Попробуйте позже."

    @staticmethod
    async def create_calendar_menu(employee):
        """Меню календаря активностей с уведомлениями"""
        counts = await MenuManager.get_notification_counts(employee.telegram_id)
        
        activities_badge = ""
        if counts['urgent_actions'] > 0:
            activities_badge = f" 🚨 ({counts['urgent_actions']} срочных)"
        elif counts['today_activities'] > 0:
            activities_badge = f" 🔔 ({counts['today_activities']} сегодня)"
        
        urgent_warning = ""
        if counts['urgent_actions'] > 0:
            urgent_warning = f"\n\n🚨 *Внимание!* У вас {counts['urgent_actions']} срочных действий, требующих подтверждения!"
        
        calendar_text = f"""
📅 *Ваши активности на этой неделе{activities_badge}*

*Понедельник:*
• 15:00 ☕️ Тайный кофе с коллегой

*Среда:*
• 13:00 🍝 Обед вслепую
• 18:00 ♟️ Шахматный турнир

*Пятница:*
• 17:00 🎲 Вечер настольных игр

*Статус:*
• Ожидающие подтверждения: {counts['today_activities']}
• Срочные действия: {counts['urgent_actions']}
{urgent_warning}

Используйте кнопки ниже для управления участием.
"""
        return calendar_text

    @staticmethod
    async def create_achievements_menu(employee):
        """Меню достижений"""
        # Получаем счетчики для контекста
        counts = await MenuManager.get_notification_counts(employee.telegram_id)

        motivation_text = ""
        if counts['today_activities'] > 0:
            motivation_text = f"\n💡 У вас {counts['today_activities']} активностей сегодня - отличный шанс получить новое достижение!"

        achievements_text = f"""
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
{motivation_text}

*Продолжайте в том же духе!* 🚀
"""
        return achievements_text

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
/notifications - Показать уведомления
/refresh - Обновить счетчики

*Частые вопросы:*
Используйте кнопки ниже для быстрых ответов на популярные вопросы.
"""
        return help_text

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
        return settings_text

    @staticmethod
    async def create_coffee_menu():
        """Меню Тайного кофе с уведомлениями"""
        coffee_text = """
☕ *Тайный кофе*

🤫 Анонимная встреча с коллегой
🎯 Матчинг каждую неделю по понедельникам

*Доступные действия:*
💬 *Написать сообщение* - отправить сообщение партнеру
📅 *Предложить встречу* - выбрать время для встречи  
📋 *Инструкция* - правила и рекомендации

💡 Для участия обновите свой профиль!
"""
        return coffee_text

    @staticmethod
    async def create_notifications_menu(user_id=None):
        """Специальное меню для просмотра уведомлений"""
        counts = await MenuManager.get_notification_counts(user_id) if user_id else {'total': 0}
        
        if counts['total'] == 0:
            return """
🔔 *Уведомления*

🎉 У вас нет непрочитанных уведомлений!

Все действия завершены, вы молодец! 💪

Если ожидали какое-то уведомление, используйте /refresh для обновления.
"""
        
        notifications_text = f"""
🔔 *Детализация уведомлений*

*Ожидающие действия:*

"""
        
        if counts['urgent_actions'] > 0:
            notifications_text += f"🚨 *Срочные действия ({counts['urgent_actions']}):*\n"
            notifications_text += "• Подтвердите участие в сегодняшних активностях\n"
            notifications_text += "• Ответьте на срочные запросы по встречам\n\n"
        
        if counts['meetings'] > 0:
            notifications_text += f"🤝 *Встречи ({counts['meetings']}):*\n"
            notifications_text += "• Ожидают вашего подтверждения\n"
            notifications_text += "• Требуют согласования времени\n\n"
        
        if counts['today_activities'] > 0:
            notifications_text += f"📅 *Активности сегодня ({counts['today_activities']}):*\n"
            notifications_text += "• Запланированы на сегодня\n"
            notifications_text += "• Требуют подготовки или подтверждения\n\n"
        
        if counts['notifications'] > 0:
            notifications_text += f"📨 *Системные уведомления ({counts['notifications']}):*\n"
            notifications_text += "• Обновления системы\n"
            notifications_text += "• Важные объявления\n\n"
        
        notifications_text += f"💡 *Всего: {counts['total']} ожидающих действий*"
        notifications_text += "\n\nИспользуйте соответствующие разделы меню для работы с уведомлениями."
        
        return notifications_text

    # Backwards-compatible aliases for older callers
    @staticmethod
    async def get_main_menu(*args, **kwargs):
        user_id = kwargs.get('user_id')
        return await MenuManager.create_main_menu_message(user_id)

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