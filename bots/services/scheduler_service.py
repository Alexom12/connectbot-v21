import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from config.settings import CONNECTBOT_SETTINGS
from activities.services.anonymous_coffee_service import anonymous_coffee_service
from activities.services.activity_manager import ActivityManager

logger = logging.getLogger(__name__)

class SchedulerService:
    """Сервис для управления планировщиком задач"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start_scheduler(self):
        """Запуск планировщика"""
        try:
            if self.is_running:
                logger.warning("⚠️ Планировщик уже запущен")
                return
            
            # Настраиваем задачи
            self._setup_jobs()
            
            # Запускаем планировщик
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Планировщик задач успешно запущен")
            
            # Запускаем немедленно создание недельных сессий при старте
            asyncio.create_task(self._create_weekly_sessions_async())
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("✅ Планировщик задач остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки планировщика: {e}")
    
    def _setup_jobs(self):
        """Настройка периодических задач"""
        
        # 1. Создание недельных сессий активностей - каждый понедельник в 09:00
        self.scheduler.add_job(
            self._create_weekly_sessions_async,
            trigger=CronTrigger(
                day_of_week='mon', 
                hour=9, 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='create_weekly_sessions',
            name='Создание недельных сессий активностей',
            replace_existing=True
        )
        
        # 2. Matching для Тайного кофе - каждый понедельник в 10:00
        self.scheduler.add_job(
            self._run_coffee_matching_async,
            trigger=CronTrigger(
                day_of_week='mon', 
                hour=10, 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='coffee_matching',
            name='Matching для Тайного кофе',
            replace_existing=True
        )
        
        # 3. Отправка напоминаний - каждый день в 09:00
        self.scheduler.add_job(
            self._send_daily_reminders_async,
            trigger=CronTrigger(
                hour=9, 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='daily_reminders',
            name='Ежедневные напоминания',
            replace_existing=True
        )
        
        # 4. Напоминания о встречах - каждый час с 08:00 до 20:00
        self.scheduler.add_job(
            self._send_meeting_reminders_async,
            trigger=CronTrigger(
                hour='8-20', 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='meeting_reminders',
            name='Напоминания о встречах',
            replace_existing=True
        )
        
        # 5. Проверка неактивных встреч - каждый день в 18:00
        self.scheduler.add_job(
            self._check_inactive_meetings_async,
            trigger=CronTrigger(
                hour=18, 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='inactive_meetings_check',
            name='Проверка неактивных встреч',
            replace_existing=True
        )
        
        # 6. Еженедельная статистика - пятница в 17:00
        self.scheduler.add_job(
            self._send_weekly_stats_async,
            trigger=CronTrigger(
                day_of_week='fri', 
                hour=17, 
                minute=0,
                timezone='Europe/Moscow'
            ),
            id='weekly_stats',
            name='Еженедельная статистика',
            replace_existing=True
        )
        
        logger.info("✅ Периодические задачи настроены")
    
    async def _create_weekly_sessions_async(self):
        """Создание недельных сессий активностей (асинхронная обертка)"""
        try:
            logger.info("🔄 Запуск создания недельных сессий...")
            manager = ActivityManager()
            success = await manager.create_weekly_sessions()
            
            if success:
                logger.info("✅ Недельные сессии успешно созданы")
            else:
                logger.error("❌ Ошибка создания недельных сессий")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в создании сессий: {e}")
    
    async def _run_coffee_matching_async(self):
        """Запуск matching для Тайного кофе (асинхронная обертка)"""
        try:
            logger.info("🔄 Запуск matching Тайного кофе...")
            success = await anonymous_coffee_service.run_weekly_matching()
            
            if success:
                logger.info("✅ Matching Тайного кофе выполнен успешно")
            else:
                logger.error("❌ Ошибка matching Тайного кофе")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в matching Тайного кофе: {e}")
    
    async def _send_daily_reminders_async(self):
        """Отправка ежедневных напоминаний"""
        try:
            logger.info("🔄 Отправка ежедневных напоминаний...")
            
            from activities.models import ActivityParticipant, ActivitySession
            from datetime import date
            from bots.handlers.notification_handlers import send_telegram_message
            
            # Получаем текущую недельную сессию
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            # Находим активные сессии на эту неделю
            sessions = ActivitySession.objects.filter(
                week_start=week_start,
                status='active'
            )
            
            reminder_count = 0
            
            async for session in sessions:
                # Получаем участников, у которых еще нет пары
                participants = ActivityParticipant.objects.filter(
                    activity_session=session,
                    subscription_status=True
                ).select_related('employee')
                
                async for participant in participants:
                    # Проверяем, есть ли у участника пара
                    has_pair = await self._check_if_has_pair(session, participant.employee)
                    
                    if not has_pair:
                        message = self._get_reminder_message(session.activity_type)
                        success = await send_telegram_message(
                            participant.employee.telegram_id, 
                            message
                        )
                        if success:
                            reminder_count += 1
            
            logger.info(f"✅ Отправлено {reminder_count} напоминаний")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний: {e}")
    
    async def _send_meeting_reminders_async(self):
        """Отправка напоминаний о предстоящих встречах"""
        try:
            logger.info("🔄 Проверка встреч для напоминаний...")
            
            from activities.models import SecretCoffeeMeeting
            from bots.handlers.notification_handlers import send_telegram_message
            
            now = timezone.now()
            reminder_time = now + timedelta(hours=1)  # Напоминать за 1 час
            
            # Находим встречи, которые начнутся в течение часа
            upcoming_meetings = SecretCoffeeMeeting.objects.filter(
                meeting_date__gte=now,
                meeting_date__lte=reminder_time,
                status='confirmed'
            ).select_related('employee1', 'employee2')
            
            reminder_count = 0
            
            async for meeting in upcoming_meetings:
                message = f"""⏰ *НАПОМИНАНИЕ О ВСТРЕЧЕ*

Через 1 час у вас запланирована встреча Тайного кофе!

🗓️ {meeting.meeting_date.strftime('%d.%m.%Y %H:%M')}
📍 {meeting.meeting_location}
🎯 Код: `{meeting.employee1_code if meeting.employee1 else meeting.employee2_code}`

Не забудьте опознавательный знак: *{meeting.recognition_sign}*"""
                
                # Отправляем обоим участникам
                success1 = await send_telegram_message(meeting.employee1.telegram_id, message)
                success2 = await send_telegram_message(meeting.employee2.telegram_id, message)
                
                if success1 or success2:
                    reminder_count += 1
            
            if reminder_count > 0:
                logger.info(f"✅ Отправлено {reminder_count} напоминаний о встречах")
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний о встречах: {e}")
    
    async def _check_inactive_meetings_async(self):
        """Проверка неактивных встреч"""
        try:
            logger.info("🔄 Проверка неактивных встреч...")
            
            from activities.models import SecretCoffeeMeeting
            from datetime import timedelta
            
            deadline = timezone.now() - timedelta(days=2)  # 2 дня без активности
            
            # Находим встречи в статусе планирования старше 2 дней
            inactive_meetings = SecretCoffeeMeeting.objects.filter(
                status='scheduling',
                created_at__lte=deadline
            ).select_related('employee1', 'employee2')
            
            inactive_count = 0
            
            async for meeting in inactive_meetings:
                # Переводим встречу в статус "не состоялась"
                meeting.status = 'failed'
                await meeting.asave()
                inactive_count += 1
                
                logger.info(f"⚠️ Встреча {meeting.meeting_id} переведена в статус 'не состоялась'")
            
            if inactive_count > 0:
                logger.info(f"✅ Проверено {inactive_count} неактивных встреч")
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки неактивных встреч: {e}")
    
    async def _send_weekly_stats_async(self):
        """Отправка еженедельной статистики админам"""
        try:
            logger.info("🔄 Подготовка еженедельной статистики...")
            
            from activities.models import ActivitySession, SecretCoffeeMeeting
            from employees.models import Employee
            from config.settings import SUPER_ADMIN_ID
            from bots.handlers.notification_handlers import send_telegram_message
            
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            # Собираем статистику
            total_sessions = await ActivitySession.objects.filter(
                week_start=week_start
            ).acount()
            
            coffee_meetings = await SecretCoffeeMeeting.objects.filter(
                activity_session__week_start=week_start
            ).acount()
            
            completed_meetings = await SecretCoffeeMeeting.objects.filter(
                activity_session__week_start=week_start,
                status='completed'
            ).acount()
            
            total_participants = await Employee.objects.filter(
                is_active=True
            ).acount()
            
            # Формируем сообщение со статистикой
            stats_message = f"""📊 *ЕЖЕНЕДЕЛЬНАЯ СТАТИСТИКА CONNECTBOT*

📅 Неделя: {week_start.strftime('%d.%m.%Y')}

🎯 Активности:
• Сессий создано: {total_sessions}
• Тайных кофе: {coffee_meetings}
• Успешных встреч: {completed_meetings}

👥 Участники:
• Всего сотрудников: {total_participants}
• Вовлеченность: {round((coffee_meetings * 2 / total_participants) * 100) if total_participants > 0 else 0}%

📈 Эффективность matching: {round((completed_meetings / coffee_meetings) * 100) if coffee_meetings > 0 else 0}%

Хороших выходных! 🎉"""
            
            # Отправляем статистику супер-админу
            if SUPER_ADMIN_ID:
                await send_telegram_message(SUPER_ADMIN_ID, stats_message)
            
            logger.info("✅ Еженедельная статистика отправлена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки статистики: {e}")
    
    async def _check_if_has_pair(self, session, employee):
        """Проверка, есть ли у сотрудника пара в сессии"""
        from activities.models import ActivityPair
        
        try:
            pair1 = await ActivityPair.objects.filter(
                activity_session=session,
                employee1=employee
            ).aexists()
            
            pair2 = await ActivityPair.objects.filter(
                activity_session=session,
                employee2=employee
            ).aexists()
            
            return pair1 or pair2
            
        except Exception:
            return False
    
    def _get_reminder_message(self, activity_type):
        """Получить текст напоминания в зависимости от типа активности"""
        messages = {
            'secret_coffee': """☕️ *НАПОМИНАНИЕ: ТАЙНЫЙ КОФЕ*

На этой неделе у вас запланирован Тайный кофе!

Если вы еще не начали планирование встречи, самое время это сделать! 🎭

Проверьте меню бота → Тайный кофе""",
            
            'chess': """♟️ *НАПОМИНАНИЕ: ШАХМАТЫ*

Не забудьте сыграть шахматную партию на этой неделе!

Найдите соперника и назначьте игру 🏆""",
            
            'ping_pong': """🏓 *НАПОМИНАНИЕ: НАСТОЛЬНЫЙ ТЕННИС*

Самое время для активной игры в настольный теннис!

Запланируйте игру с коллегой 🎯"""
        }
        
        return messages.get(activity_type, "🎯 Не забудьте поучаствовать в активностях на этой неделе!")

    def get_scheduler_status(self):
        """Получить статус планировщика"""
        if not self.scheduler.running:
            return {
                'status': 'stopped',
                'jobs': []
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'None',
                'trigger': str(job.trigger)
            })
        
        return {
            'status': 'running',
            'job_count': len(jobs),
            'jobs': jobs
        }

# Глобальный экземпляр планировщика
scheduler_service = SchedulerService()