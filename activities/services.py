import logging
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import ActivitySession, ActivityParticipant, ActivityPair, ACTIVITY_TYPES

logger = logging.getLogger(__name__)

class ActivityManager:
    """Сервис управления активностями"""
    
    async def create_weekly_sessions(self):
        """Создание еженедельных сессий для всех активностей"""
        try:
            # Определяем начало следующей недели (понедельник)
            today = timezone.now().date()
            days_ahead = 0 - today.weekday()  # Понедельник = 0
            if days_ahead <= 0:  # Если сегодня уже понедельник или позже
                days_ahead += 7
            next_monday = today + timedelta(days=days_ahead)
            
            # Создаем сессии для всех типов активностей
            for activity_type, _ in ACTIVITY_TYPES:
                session, created = await sync_to_async(ActivitySession.objects.get_or_create)(
                    activity_type=activity_type,
                    week_start=next_monday,
                    defaults={'status': 'planned'}
                )
                if created:
                    logger.info(f"Создана сессия {activity_type} на {next_monday}")
                else:
                    logger.info(f"Сессия {activity_type} на {next_monday} уже существует")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания недельных сессий: {e}")
            return False
    
    async def get_participants(self, activity_type, week_start=None):
        """Получение участников для активности"""
        try:
            if not week_start:
                # По умолчанию текущая неделя
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
            
            session = await sync_to_async(ActivitySession.objects.get)(
                activity_type=activity_type,
                week_start=week_start
            )
            
            participants = await sync_to_async(list)(
                ActivityParticipant.objects.filter(
                    activity_session=session,
                    subscription_status=True
                ).select_related('employee')
            )
            
            return [participant.employee for participant in participants]
            
        except ActivitySession.DoesNotExist:
            logger.warning(f"Сессия {activity_type} на {week_start} не найдена")
            return []
        except Exception as e:
            logger.error(f"Ошибка получения участников: {e}")
            return []
    
    async def form_pairs(self, activity_type, participants, week_start=None):
        """Формирование пар через Java микросервис"""
        try:
            if not week_start:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
            
            session = await sync_to_async(ActivitySession.objects.get)(
                activity_type=activity_type,
                week_start=week_start
            )
            
            # TODO: Интеграция с Java микросервисом для matching
            # Временно создаем простые пары
            pairs = []
            for i in range(0, len(participants)-1, 2):
                if i+1 < len(participants):
                    pair = await sync_to_async(ActivityPair.objects.create)(
                        activity_session=session,
                        employee1=participants[i],
                        employee2=participants[i+1]
                    )
                    pairs.append(pair)
            
            logger.info(f"Создано {len(pairs)} пар для {activity_type}")
            return pairs
            
        except Exception as e:
            logger.error(f"Ошибка формирования пар: {e}")
            return []