"""
Сервис для анализа контекста пользователя и предоставления умных подсказок
"""
import logging
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from employees.models import Employee
from activities.models import Activity, Meeting
from bots.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class ContextService:
    """Сервис для анализа контекста пользователя и умных подсказок"""
    
    @staticmethod
    async def get_user_context(user_id):
        """
        Анализирует текущий контекст пользователя
        
        Returns:
            dict: Контекст пользователя с рекомендациями
        """
        try:
            employee = await Employee.objects.aget(telegram_id=user_id)
            
            # Получаем базовые данные
            now = timezone.now()
            current_hour = now.hour
            current_weekday = now.weekday()
            current_date = now.date()
            
            # Анализируем активность пользователя
            activity_profile = await ContextService._analyze_activity_profile(employee)
            time_context = await ContextService._analyze_time_context(current_hour, current_weekday)
            notification_context = await notification_service.get_notification_summary(user_id)
            
            # Формируем контекст
            context = {
                'user_id': user_id,
                'employee': employee,
                'time_context': time_context,
                'activity_profile': activity_profile,
                'notifications': notification_context,
                'quick_actions': await ContextService._get_quick_actions(
                    employee, time_context, notification_context
                ),
                'smart_tips': await ContextService._get_smart_tips(
                    activity_profile, time_context, notification_context
                ),
                'priority_level': await ContextService._calculate_priority_level(notification_context)
            }
            
            logger.debug(f"Сформирован контекст для пользователя {user_id}: {context['priority_level']}")
            return context
            
        except Exception as e:
            logger.error(f"Ошибка анализа контекста пользователя {user_id}: {e}")
            return await ContextService._get_default_context(user_id)
    
    @staticmethod
    async def _analyze_activity_profile(employee):
        """Анализирует профиль активности пользователя"""
        try:
            # Анализ участия в активностях
            total_activities = await Activity.objects.filter(
                participants__employee=employee
            ).acount()
            
            # Анализ встреч
            # SecretCoffeeMeeting stores participants in employee1/employee2
            from django.db.models import Q
            total_meetings = await Meeting.objects.filter(
                Q(employee1=employee) | Q(employee2=employee)
            ).acount()
            
            # Анализ частоты участия (последние 30 дней)
            month_ago = timezone.now() - timedelta(days=30)
            recent_activities = await Activity.objects.filter(
                participants__employee=employee,
                scheduled_date__gte=month_ago
            ).acount()
            
            # Определяем уровень активности
            if recent_activities >= 10:
                activity_level = "high"
                activity_label = "Активный участник 🏆"
            elif recent_activities >= 5:
                activity_level = "medium" 
                activity_label = "Регулярный участник 👍"
            elif recent_activities >= 1:
                activity_level = "low"
                activity_label = "Новичок 🌱"
            else:
                activity_level = "new"
                activity_label = "Новый пользователь 🎯"
            
            return {
                'total_activities': total_activities,
                'total_meetings': total_meetings,
                'recent_activities': recent_activities,
                'activity_level': activity_level,
                'activity_label': activity_label,
                'experience_level': await ContextService._calculate_experience_level(total_activities)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа профиля активности: {e}")
            return {
                'total_activities': 0,
                'total_meetings': 0,
                'recent_activities': 0,
                'activity_level': 'new',
                'activity_label': 'Новый пользователь 🎯',
                'experience_level': 'beginner'
            }
    
    @staticmethod
    async def _analyze_time_context(current_hour, current_weekday):
        """Анализирует временной контекст"""
        # Определяем время суток
        if 5 <= current_hour < 12:
            time_of_day = "morning"
            time_label = "Утро ☀️"
            time_tip = "Отличное время для планирования дня!"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon" 
            time_label = "День 🏢"
            time_tip = "Рабочее время - идеально для встреч!"
        elif 17 <= current_hour < 22:
            time_of_day = "evening"
            time_label = "Вечер 🌙"
            time_tip = "Время для неформального общения"
        else:
            time_of_day = "night"
            time_label = "Ночь 🌙"
            time_tip = "Поздний час, отдыхайте!"
        
        # Определяем день недели
        if current_weekday == 0:
            day_context = "week_start"
            day_tip = "Начало недели - время планировать встречи!"
        elif current_weekday == 4:
            day_context = "week_end"
            day_tip = "Конец недели - подводим итоги!"
        elif current_weekday >= 5:
            day_context = "weekend"
            day_tip = "Выходные - время для неформальных активностей!"
        else:
            day_context = "weekday"
            day_tip = "Рабочий день - участвуйте в активностях!"
        
        return {
            'time_of_day': time_of_day,
            'time_label': time_label,
            'time_tip': time_tip,
            'day_context': day_context,
            'day_tip': day_tip,
            'current_hour': current_hour,
            'current_weekday': current_weekday
        }
    
    @staticmethod
    async def _calculate_experience_level(total_activities):
        """Определяет уровень опыта пользователя"""
        if total_activities >= 20:
            return "expert"
        elif total_activities >= 10:
            return "advanced"
        elif total_activities >= 5:
            return "intermediate"
        elif total_activities >= 1:
            return "beginner"
        else:
            return "new"
    
    @staticmethod
    async def _calculate_priority_level(notification_context):
        """Определяет уровень приоритета на основе уведомлений"""
        counts = notification_context['counts']
        
        if counts['urgent_actions'] > 0:
            return "urgent"
        elif counts['total'] >= 5:
            return "high"
        elif counts['total'] >= 3:
            return "medium"
        elif counts['total'] >= 1:
            return "low"
        else:
            return "none"
    
    @staticmethod
    async def _get_quick_actions(employee, time_context, notification_context):
        """Генерирует быстрые действия на основе контекста"""
        counts = notification_context['counts']
        quick_actions = []
        
        # Действия на основе уведомлений
        if counts['urgent_actions'] > 0:
            quick_actions.append("🚨 Подтвердить срочные действия")
        
        if counts['meetings'] > 0:
            quick_actions.append("🤝 Ответить на встречи")
        
        if counts['today_activities'] > 0:
            quick_actions.append("📅 Подтвердить участие")
        
        # Действия на основе времени
        if time_context['time_of_day'] == "morning":
            quick_actions.append("📋 Планирование на день")
        
        if time_context['day_context'] == "week_start":
            quick_actions.append("🗓️ Настройка на неделю")
        
        if time_context['day_context'] == "week_end":
            quick_actions.append("📊 Итоги недели")
        
        # Действия на основе опыта
        activity_profile = await ContextService._analyze_activity_profile(employee)
        if activity_profile['experience_level'] == "new":
            quick_actions.append("🎯 Начать с простых активностей")
        
        # Ограничиваем количество действий
        return quick_actions[:4]
    
    @staticmethod
    async def _get_smart_tips(activity_profile, time_context, notification_context):
        """Генерирует умные подсказки на основе контекста"""
        tips = []
        counts = notification_context['counts']
        
        # Подсказки на основе уведомлений
        if counts['urgent_actions'] > 0:
            tips.append("🚨 Не забудьте про срочные действия!")
        
        if counts['total'] == 0:
            tips.append("🎉 Все задачи выполнены! Можете отдохнуть или выбрать новые активности.")
        
        # Подсказки на основе времени
        tips.append(time_context['time_tip'])
        tips.append(time_context['day_tip'])
        
        # Подсказки на основе активности
        if activity_profile['activity_level'] == "new":
            tips.append("💡 Начните с Тайного кофе - это отличный способ познакомиться с коллегами!")
        elif activity_profile['activity_level'] == "low":
            tips.append("🌟 Попробуйте разные активности для получения достижений!")
        elif activity_profile['activity_level'] == "high":
            tips.append("🏆 Вы - звезда активностей! Продолжайте в том же духе!")
        
        # Подсказки на основе дня недели
        if time_context['current_weekday'] == 0:  # Понедельник
            tips.append("📅 Понедельник - идеальный день для планирования встреч на неделю!")
        elif time_context['current_weekday'] == 4:  # Пятница
            tips.append("🎯 Пятница - время подводить итоги и планировать выходные активности!")
        
        return tips
    
    @staticmethod
    async def _get_default_context(user_id):
        """Возвращает контекст по умолчанию"""
        return {
            'user_id': user_id,
            'employee': None,
            'time_context': {
                'time_of_day': 'day',
                'time_label': 'День 🏢',
                'time_tip': 'Добро пожаловать!',
                'day_context': 'weekday',
                'day_tip': 'Хорошего дня!',
                'current_hour': 12,
                'current_weekday': 0
            },
            'activity_profile': {
                'total_activities': 0,
                'total_meetings': 0,
                'recent_activities': 0,
                'activity_level': 'new',
                'activity_label': 'Новый пользователь 🎯',
                'experience_level': 'beginner'
            },
            'notifications': {
                'counts': {'total': 0},
                'has_urgent': False,
                'has_pending': False,
                'primary_alert': None
            },
            'quick_actions': ["🎯 Начать знакомство", "📚 Изучить возможности"],
            'smart_tips': ["💡 Используйте кнопки для навигации", "🔔 Числа показывают ожидающие действия"],
            'priority_level': 'none'
        }
    
    @staticmethod
    async def get_contextual_welcome(user_id):
        """Генерирует приветственное сообщение с учетом контекста"""
        context = await ContextService.get_user_context(user_id)
        
        welcome_parts = []
        
        # Приветствие на основе времени
        time_ctx = context['time_context']
        welcome_parts.append(f"{time_ctx['time_label']}")
        
        # Информация об активности
        activity_ctx = context['activity_profile']
        welcome_parts.append(f"Ваш статус: {activity_ctx['activity_label']}")
        
        # Уведомления
        notif_ctx = context['notifications']
        if notif_ctx['has_urgent']:
            welcome_parts.append("🚨 Есть срочные действия!")
        elif notif_ctx['has_pending']:
            welcome_parts.append("🔔 Есть ожидающие действия")
        else:
            welcome_parts.append("🎉 Все задачи выполнены!")
        
        # Быстрые действия
        if context['quick_actions']:
            welcome_parts.append("💡 Быстрые действия: " + ", ".join(context['quick_actions'][:2]))
        
        return "\n".join(welcome_parts)
    
    @staticmethod
    async def get_adaptive_menu_suggestions(user_id):
        """Предлагает адаптивные suggestions для меню"""
        context = await ContextService.get_user_context(user_id)
        
        suggestions = {
            'highlight_section': None,
            'recommended_actions': [],
            'educational_tips': []
        }
        
        # Определяем подсвечиваемый раздел
        if context['notifications']['has_urgent']:
            suggestions['highlight_section'] = 'calendar'
        elif context['activity_profile']['experience_level'] == 'new':
            suggestions['highlight_section'] = 'interests'
        elif context['time_context']['day_context'] == 'week_start':
            suggestions['highlight_section'] = 'coffee'
        
        # Рекомендуемые действия
        suggestions['recommended_actions'] = context['quick_actions']
        
        # Образовательные подсказки
        suggestions['educational_tips'] = context['smart_tips']
        
        return suggestions
    
    @staticmethod
    async def log_user_interaction(user_id, action_type, menu_item, success=True):
        """Логирует взаимодействие пользователя для улучшения контекста"""
        try:
            # TODO: Реализовать сохранение в базу для ML анализа
            logger.info(f"Логирование взаимодействия: user={user_id}, action={action_type}, item={menu_item}, success={success}")
            
            # Очищаем кэш контекста при значимых действиях
            if action_type in ['completed_task', 'joined_activity', 'confirmed_meeting']:
                # В будущем здесь будет обновление ML модели
                pass
                
            return True
        except Exception as e:
            logger.error(f"Ошибка логирования взаимодействия: {e}")
            return False


# Глобальный экземпляр сервиса
context_service = ContextService()