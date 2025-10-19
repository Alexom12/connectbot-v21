# config/scheduler.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

logger = logging.getLogger(__name__)

def schedule_feedback_job():
    """
    Запускает Django-команду 'schedule_feedback'.
    """
    try:
        logger.info("Запуск задачи 'schedule_feedback'...")
        call_command('schedule_feedback')
        logger.info("Задача 'schedule_feedback' успешно выполнена.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи 'schedule_feedback': {e}", exc_info=True)

def start():
    """
    Настраивает и запускает планировщик задач.
    """
    scheduler = BackgroundScheduler()
    
    # Добавляем задачу, которая будет выполняться каждый час
    scheduler.add_job(
        schedule_feedback_job,
        'interval',
        hours=1,
        id='schedule_feedback_job',  # Уникальный ID для задачи
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Планировщик запущен... Задачи будут выполняться в фоновом режиме.")
