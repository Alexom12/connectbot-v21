# activities/management/commands/schedule_feedback.py

import logging
import asyncio
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from activities.models import SecretCoffeeMeeting
from bots.notification_service import NotificationService
from bots.shared_bot import bot_manager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Django-команда для планирования сбора обратной связи по завершенным встречам.
    """
    help = 'Schedules feedback collection for completed meetings.'

    def handle(self, *args, **options):
        asyncio.run(self.a_handle(*args, **options))

    async def a_handle(self, *args, **options):
        self.stdout.write("Начинаю планирование сбора обратной связи...")
        
        try:
            bot = await bot_manager.get_bot()
            notification_service = NotificationService(bot)

            meetings_to_schedule = SecretCoffeeMeeting.objects.select_related(
                'employee1', 'employee2'
            ).filter(
                status='completed',
                feedback_deadline__isnull=True
            )
            
            if not await meetings_to_schedule.aexists():
                self.stdout.write(self.style.SUCCESS("Нет встреч для планирования."))
                return

            successful_schedules = 0
            async for meeting in meetings_to_schedule:
                deadline = timezone.now() + timedelta(hours=48)
                meeting.feedback_deadline = deadline
                await meeting.asave(update_fields=['feedback_deadline'])

                logger.info(f"Для встречи {meeting.id} установлен дедлайн: {deadline}")

                try:
                    participant_ids = [
                        meeting.employee1.telegram_id,
                        meeting.employee2.telegram_id
                    ]
                    
                    for user_id in participant_ids:
                        if user_id:
                            partner = await meeting.aget_partner(user_id)
                            partner_name = partner.full_name if partner else "вашим коллегой"
                            message = (
                                f"🤝 Ваша встреча с {partner_name} завершена! "
                                f"Пожалуйста, оставьте отзыв, чтобы мы могли сделать следующие встречи еще лучше.\n\n"
                                f"Нажмите /feedback, чтобы начать."
                            )
                            await notification_service.send_notification(user_id, message)
                    
                    logger.info(f"Уведомления для встречи {meeting.id} отправлены.")
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомлений для встречи {meeting.id}: {e}")

                successful_schedules += 1

            self.stdout.write(self.style.SUCCESS(
                f"Успешно запланирован сбор отзывов для {successful_schedules} встреч."
            ))

        except Exception as e:
            logger.error(f"Ошибка в команде schedule_feedback: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Произошла ошибка: {e}"))
        # finally:
        #     # Управление соединением теперь в BotManager, здесь закрывать не нужно
        #     pass

