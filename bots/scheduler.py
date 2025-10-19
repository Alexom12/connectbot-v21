# bots/scheduler.py

import logging
from datetime import timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from django.utils import timezone
from activities.services import feedback_service
from bots.bot_instance import get_bot_instance

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def send_feedback_request(meeting_id: int):
    """
    Отправляет участникам встречи запрос на оставление отзыва.
    """
    bot = get_bot_instance()
    if not bot:
        logger.error("Не удалось получить экземпляр бота для отправки запроса на отзыв.")
        return

    try:
        meeting = await feedback_service.get_meeting_by_id(meeting_id)
        if not meeting or meeting.feedback_collected:
            logger.info(f"Встреча {meeting_id} не найдена или отзывы уже собраны. Задача отменена.")
            return

        participant_ids = await feedback_service.get_meeting_participant_ids(meeting_id)

        for user_id in participant_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="Привет! Недавно у вас состоялась встреча в рамках Secret Coffee. "
                         "Пожалуйста, уделите минуту, чтобы оставить отзыв. "
                         "Это поможет нам сделать будущие встречи лучше!\n\n"
                         "Используйте команду /feedback, чтобы начать.",
                )
                logger.info(f"Запрос на отзыв для встречи {meeting_id} отправлен пользователю {user_id}.")
            except Exception as e:
                logger.error(f"Не удалось отправить запрос на отзыв пользователю {user_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка в задаче send_feedback_request для встречи {meeting_id}: {e}", exc_info=True)


async def schedule_feedback_collection_for_meeting(meeting_id: int):
    """
    Планирует задачи по сбору обратной связи для конкретной встречи.
    """
    try:
        meeting = await feedback_service.get_meeting_by_id(meeting_id)
        if not meeting:
            logger.warning(f"Попытка запланировать сбор для несуществующей встречи {meeting_id}.")
            return

        # 1. Запланировать немедленный (или с небольшой задержкой) запрос на отзыв
        # Задержка в 1 час после встречи
        run_time_request = meeting.date + timedelta(hours=1)
        if run_time_request > timezone.now():
            scheduler.add_job(
                send_feedback_request,
                "date",
                run_date=run_time_request,
                args=[meeting_id],
                id=f"feedback_request_{meeting_id}",
                replace_existing=True,
            )
            logger.info(f"Запланирован запрос на отзыв для встречи {meeting_id} на {run_time_request}.")

        # 2. Запланировать напоминание (например, за 1 день до дедлайна)
        if meeting.feedback_deadline:
            reminder_time = meeting.feedback_deadline - timedelta(days=1)
            if reminder_time > timezone.now():
                # В реальной реализации здесь будет задача, которая проверяет, кто еще не оставил отзыв
                # и отправляет напоминание только им. Для простоты пока опустим.
                logger.info(f"Напоминание для встречи {meeting_id} будет запланировано на {reminder_time}.")

        # 3. Запланировать финальную агрегацию результатов
        if meeting.feedback_deadline:
            aggregation_time = meeting.feedback_deadline + timedelta(minutes=5)
            if aggregation_time > timezone.now():
                scheduler.add_job(
                    feedback_service.calculate_and_save_average_rating,
                    "date",
                    run_date=aggregation_time,
                    args=[meeting_id],
                    id=f"feedback_aggregation_{meeting_id}",
                    replace_existing=True,
                )
                logger.info(f"Запланирована агрегация отзывов для встречи {meeting_id} на {aggregation_time}.")

    except Exception as e:
        logger.error(f"Ошибка при планировании сбора отзывов для встречи {meeting_id}: {e}", exc_info=True)


async def check_for_new_meetings_to_schedule():
    """
    Периодически проверяет наличие новых встреч, для которых нужно запланировать сбор обратной связи.
    """
    logger.debug("Проверка наличия новых встреч для планирования сбора отзывов...")
    try:
        meetings = await feedback_service.get_meetings_needing_feedback_scheduling()
        for meeting in meetings:
            await schedule_feedback_collection_for_meeting(meeting.id)
            # Помечаем, что задачи для этой встречи запланированы
            await feedback_service.mark_meeting_as_scheduled(meeting.id)

    except Exception as e:
        logger.error(f"Ошибка в периодической задаче 'check_for_new_meetings_to_schedule': {e}", exc_info=True)


def start_scheduler():
    """
    Запускает планировщик и добавляет периодическую задачу.
    """
    try:
        if not scheduler.running:
            scheduler.add_job(
                check_for_new_meetings_to_schedule,
                "interval",
                minutes=15, # Проверять каждые 15 минут
                id="check_new_meetings",
                replace_existing=True,
            )
            scheduler.start()
            logger.info("Планировщик задач запущен. Проверка новых встреч каждые 15 минут.")
        else:
            logger.info("Планировщик уже запущен.")
    except Exception as e:
        logger.error(f"Не удалось запустить планировщик: {e}", exc_info=True)


def stop_scheduler():
    """
    Останавливает планировщик.
    """
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Планировщик задач остановлен.")
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}", exc_info=True)
