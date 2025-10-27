"""
Сервис для работы с уведомлениями и счетчиками
"""
import logging
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q
from employees.models import Employee
from activities.models import Activity, Meeting
from bots.services.redis_service import redis_service
from datetime import timedelta

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для управления уведомлениями и счетчиками"""
    
    @staticmethod
    async def get_user_notification_counts(user_id):
        """
        Получает количество непрочитанных уведомлений и ожидающих действий для пользователя
        
        Returns:
            dict: Словарь с счетчиками уведомлений
        """
        try:
            employee = await Employee.objects.aget(telegram_id=user_id)
            
            # ВРЕМЕННО ОТКЛЮЧЕНО: Проверяем кэш Redis сначала
            # cache_key = f"notifications:{user_id}"
            # try:
            #     cached_counts = await sync_to_async(redis_service.get_cache)(cache_key)
            # except Exception as e:
            #     logger.warning(f"Не удалось получить кэш из redis для {user_id}: {e}")
            #     cached_counts = None

            # if cached_counts:
            #     logger.debug(f"Возвращаем кэшированные счетчики для пользователя {user_id}")
            #     return cached_counts
            
            today = timezone.now().date()
            
            # Подсчет ожидающих встреч (требующих действий пользователя)
            pending_meetings = await Meeting.objects.filter(
                Q(employee1=employee) | Q(employee2=employee),
                status__in=['pending_confirmation', 'awaiting_response']
            ).acount()
            
            # Подсчет активностей на сегодня - ИСПРАВЛЕНО: убрали __date для DateField
            today_activities = await Activity.objects.filter(
                participants__employee=employee,
                scheduled_date=today,  # Поле DateField, используем прямое сравнение
                status='scheduled'
            ).acount()
            
            # Подсчет активностей на этой неделе - ИСПРАВЛЕНО
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            week_activities = await Activity.objects.filter(
                participants__employee=employee,
                scheduled_date__gte=week_start,  # Для диапазона используем gte/lte
                scheduled_date__lte=week_end,
                status='scheduled'
            ).acount()
            
            # Подсчет непрочитанных системных уведомлений
            unread_notifications = await NotificationService._get_unread_system_notifications_count(user_id)
            
            # Подсчет срочных действий (дедлайны сегодня) - ВРЕМЕННО ОТКЛЮЧЕНО
            urgent_actions = await NotificationService._get_urgent_actions_count(employee, today)
            
            counts = {
                'meetings': pending_meetings,
                'today_activities': today_activities,
                'week_activities': week_activities,
                'notifications': unread_notifications,
                'urgent_actions': urgent_actions,
                'total': pending_meetings + today_activities + unread_notifications + urgent_actions
            }
            
            # ВРЕМЕННО ОТКЛЮЧЕНО: Сохраняем в кэш на 5 минут
            # try:
            #     await sync_to_async(redis_service.set_cache)(cache_key, counts, 300)
            # except Exception as e:
            #     logger.warning(f"Не удалось сохранить кэш в redis для {user_id}: {e}")
            
            logger.debug(f"Рассчитаны счетчики для пользователя {user_id}: {counts}")
            return counts
            
        except Employee.DoesNotExist:
            logger.warning(f"Пользователь {user_id} не найден в базе данных")
            return NotificationService._get_default_counts()
        except Exception as e:
            logger.error(f"Ошибка получения счетчиков уведомлений для пользователя {user_id}: {e}")
            return NotificationService._get_default_counts()
    
    @staticmethod
    async def _get_unread_system_notifications_count(user_id):
        """
        Получает количество непрочитанных системных уведомлений
        TODO: Реализовать когда будет модель SystemNotification
        """
        # Заглушка - в реальной системе здесь будет запрос к модели уведомлений
        return 0
    
    @staticmethod
    async def _get_urgent_actions_count(employee, today):
        """
        Получает количество срочных действий (дедлайны сегодня)
        ВРЕМЕННО ОТКЛЮЧЕНО: возвращает 0, пока не будет исправлена модель
        """
        try:
            # ВРЕМЕННО ОТКЛЮЧЕНО: Активности, которые требуют подтверждения сегодня
            # Поле requires_confirmation не существует в модели Activity
            # urgent_activities = await Activity.objects.filter(
            #     participants__employee=employee,
            #     scheduled_date=today,
            #     status='scheduled',
            #     requires_confirmation=True  # Этого поля нет в модели!
            # ).acount()
            
            # ВРЕМЕННО ОТКЛЮЧЕНО: Встречи, которые требуют ответа сегодня
            # urgent_meetings = await Meeting.objects.filter(
            #     Q(employee1=employee) | Q(employee2=employee),
            #     status='awaiting_response',
            #     created_at__date=today
            # ).acount()
            
            # return urgent_activities + urgent_meetings
            return 0  # Временно возвращаем 0
            
        except Exception as e:
            logger.error(f"Ошибка получения срочных действий: {e}")
            return 0
    
    @staticmethod
    def _get_default_counts():
        """Возвращает счетчики по умолчанию"""
        return {
            'meetings': 0,
            'today_activities': 0,
            'week_activities': 0,
            'notifications': 0,
            'urgent_actions': 0,
            'total': 0
        }
    
    @staticmethod
    async def clear_notification_cache(user_id):
        """Очищает кэш уведомлений для пользователя"""
        try:
            cache_key = f"notifications:{user_id}"
            try:
                await sync_to_async(redis_service.delete_cache)(cache_key)
            except Exception as e:
                logger.warning(f"Не удалось удалить ключ кэша {cache_key}: {e}")
            logger.debug(f"Кэш уведомлений очищен для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки кэша уведомлений для пользователя {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_notification_summary(user_id):
        """
        Получает детальную сводку по уведомлениям
        """
        counts = await NotificationService.get_user_notification_counts(user_id)
        
        summary = {
            'counts': counts,
            'has_urgent': counts['urgent_actions'] > 0,
            'has_pending': counts['total'] > 0,
            'primary_alert': None
        }
        
        # Определяем основной тип уведомления для показа
        if counts['urgent_actions'] > 0:
            summary['primary_alert'] = 'urgent'
        elif counts['meetings'] > 0:
            summary['primary_alert'] = 'meetings'
        elif counts['today_activities'] > 0:
            summary['primary_alert'] = 'activities'
        elif counts['notifications'] > 0:
            summary['primary_alert'] = 'notifications'
        
        return summary
    
    @staticmethod
    async def mark_notification_as_read(user_id, notification_type, item_id=None):
        """
        Помечает уведомление как прочитанное
        TODO: Реализовать когда будет система уведомлений
        """
        try:
            # Очищаем кэш при изменении статуса уведомлений
            await NotificationService.clear_notification_cache(user_id)
            logger.info(f"Уведомление помечено как прочитанное для пользователя {user_id}, тип: {notification_type}")
            return True
        except Exception as e:
            logger.error(f"Ошибка пометки уведомления как прочитанного: {e}")
            return False
    
    @staticmethod
    async def send_instant_notification(user_id, message, notification_type="info"):
        """
        Отправляет мгновенное уведомление пользователю
        TODO: Интегрировать с Telegram API когда будет доступ к application
        """
        try:
            # Логируем уведомление
            logger.info(f"Уведомление для пользователя {user_id}: {message} (тип: {notification_type})")
            
            # В реальной системе здесь будет отправка через Telegram Bot API
            # await application.bot.send_message(chat_id=user_id, text=message)
            
            # Очищаем кэш счетчиков
            await NotificationService.clear_notification_cache(user_id)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_notification_history(user_id, limit=10):
        """
        Получает историю уведомлений пользователя
        TODO: Реализовать когда будет модель Notification
        """
        # Заглушка - возвращаем тестовые данные
        return [
            {
                'id': 1,
                'type': 'activity_reminder',
                'title': 'Напоминание о встрече',
                'message': 'У вас запланирована встреча через 2 часа',
                'created_at': '2024-01-15 10:00:00',
                'is_read': False
            },
            {
                'id': 2,
                'type': 'system',
                'title': 'Обновление системы',
                'message': 'Бот был обновлен до версии 2.1',
                'created_at': '2024-01-14 15:30:00',
                'is_read': True
            }
        ]
    
    @staticmethod
    async def schedule_daily_notifications():
        """
        Запланировать ежедневные уведомления для всех пользователей
        Вызывается планировщиком
        """
        try:
            # Получаем всех активных пользователей
            active_users = await sync_to_async(list)(
                Employee.objects.filter(
                    authorized=True,
                    telegram_id__isnull=False
                ).values_list('telegram_id', flat=True)
            )
            
            scheduled_count = 0
            for user_id in active_users:
                try:
                    # Получаем сводку по уведомлениям
                    summary = await NotificationService.get_notification_summary(user_id)
                    
                    if summary['has_pending']:
                        # Отправляем ежедневную сводку
                        message = NotificationService._format_daily_summary(summary['counts'])
                        # await NotificationService.send_instant_notification(user_id, message)
                        scheduled_count += 1
                        
                except Exception as e:
                    logger.error(f"Ошибка планирования уведомления для пользователя {user_id}: {e}")
                    continue
            
            logger.info(f"Запланировано ежедневных уведомлений: {scheduled_count} для {len(active_users)} пользователей")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"Ошибка планирования ежедневных уведомлений: {e}")
            return 0
    
    @staticmethod
    def _format_daily_summary(counts):
        """Форматирует ежедневную сводку уведомлений"""
        if counts['total'] == 0:
            return "🎉 На сегодня у вас нет ожидающих действий! Хорошего дня!"
        
        message = "🔔 *Ежедневная сводка*\n\n"
        
        if counts['urgent_actions'] > 0:
            message += f"🚨 Срочные действия: {counts['urgent_actions']}\n"
        
        if counts['meetings'] > 0:
            message += f"🤝 Ожидающие встречи: {counts['meetings']}\n"
        
        if counts['today_activities'] > 0:
            message += f"📅 Активности сегодня: {counts['today_activities']}\n"
        
        if counts['notifications'] > 0:
            message += f"📨 Непрочитанные уведомления: {counts['notifications']}\n"
        
        message += f"\n💡 Всего ожидающих действий: {counts['total']}"
        message += "\n\nИспользуйте команду /notifications для детального просмотра."
        
        return message


# Создаем глобальный экземпляр сервиса
notification_service = NotificationService()