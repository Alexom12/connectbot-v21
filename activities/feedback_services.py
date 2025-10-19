# activities/feedback_service.py

import logging
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Avg
from django.db import models

from prometheus_client import Counter, Gauge

from .models import SecretCoffeeMeeting, MeetingFeedback, Employee

logger = logging.getLogger(__name__)


class FeedbackMetrics:
    """
    Класс для управления метриками Prometheus, связанными с обратной связью.
    """

    # Счетчик отправленных отзывов с меткой для оценки
    feedbacks_submitted = Counter(
        "feedbacks_submitted_total",
        "Total number of feedbacks submitted",
        ["rating"],
    )

    # Gauge для среднего рейтинга встреч
    average_rating = Gauge(
        "average_meeting_rating",
        "Average rating for a completed meeting",
        ["meeting_id"],
    )

    # Счетчик ошибок при обработке отзывов
    feedback_errors = Counter(
        "feedback_processing_errors_total",
        "Total errors encountered during feedback processing",
    )


class FeedbackService:
    """
    Сервис для управления логикой сбора и обработки обратной связи.
    Все методы, работающие с Django ORM, обернуты в `sync_to_async`.
    """

    @staticmethod
    @sync_to_async
    def submit_feedback(meeting_id: int, user_telegram_id: int, rating: int, anonymous_feedback: str, suggestions: str):
        """
        Сохраняет отзыв пользователя о встрече.
        """
        try:
            meeting = SecretCoffeeMeeting.objects.get(id=meeting_id)
            employee = Employee.objects.get(telegram_id=user_telegram_id)

            feedback, created = MeetingFeedback.objects.update_or_create(
                meeting=meeting,
                employee=employee,
                defaults={
                    "rating": rating, 
                    "anonymous_feedback": anonymous_feedback,
                    "suggestions": suggestions
                },
            )

            logger.info(
                f"Отзыв {'создан' if created else 'обновлен'} для встречи {meeting_id} пользователем {employee.telegram_username}"
            )

            # Обновляем метрику
            FeedbackMetrics.feedbacks_submitted.labels(rating=rating).inc()

            return feedback

        except (SecretCoffeeMeeting.DoesNotExist, Employee.DoesNotExist) as e:
            logger.error(f"Не удалось найти встречу или сотрудника при сохранении отзыва: {e}")
            FeedbackMetrics.feedback_errors.inc()
            raise ValueError("Meeting or Employee not found.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при сохранении отзыва: {e}", exc_info=True)
            FeedbackMetrics.feedback_errors.inc()
            raise

    @staticmethod
    @sync_to_async
    def get_pending_feedbacks_for_user(user_telegram_id: int):
        """
        Возвращает список встреч, для которых пользователь еще не оставил отзыв
        и дедлайн еще не прошел.
        """
        now = timezone.now()
        user = Employee.objects.get(telegram_id=user_telegram_id)

        # Встречи, где пользователь - участник, статус 'завершена', дедлайн не прошел
        meetings_to_review = SecretCoffeeMeeting.objects.filter(
            models.Q(employee1=user) | models.Q(employee2=user),
            status='completed',
            feedback_deadline__gt=now,
        ).exclude(
            feedbacks__employee=user  # Исключаем те, где отзыв уже есть
        )

        return list(meetings_to_review)

    @staticmethod
    @sync_to_async
    def calculate_and_save_average_rating(meeting_id: int):
        """
        Вычисляет средний рейтинг для встречи и сохраняет его.
        Помечает встречу как "отзывы собраны".
        """
        try:
            meeting = SecretCoffeeMeeting.objects.get(id=meeting_id)
            
            # Вычисляем средний рейтинг
            average = meeting.feedbacks.aggregate(avg_rating=Avg("rating"))["avg_rating"]

            if average is not None:
                meeting.average_rating = round(average, 2)
                meeting.feedback_collected = True
                meeting.save(update_fields=['average_rating', 'feedback_collected'])

                # Обновляем метрику
                FeedbackMetrics.average_rating.labels(meeting_id=meeting_id).set(meeting.average_rating)

                logger.info(f"Средний рейтинг для встречи {meeting_id} рассчитан и сохранен: {meeting.average_rating}")
            else:
                logger.warning(f"Для встречи {meeting_id} нет отзывов для расчета рейтинга.")

        except SecretCoffeeMeeting.DoesNotExist:
            logger.error(f"Попытка рассчитать рейтинг для несуществующей встречи {meeting_id}")
            FeedbackMetrics.feedback_errors.inc()

    # Методы ниже используют несуществующее поле scheduling_status, временно закомментируем их
    # @staticmethod
    # @sync_to_async
    # def get_meetings_needing_feedback_scheduling():
    #     """
    #     Возвращает завершенные встречи, для которых еще не были запланированы задачи по сбору отзывов.
    #     """
    #     return list(SecretCoffeeMeeting.objects.filter(
    #         status='completed',
    #         scheduling_status='pending'
    #     ))

    # @staticmethod
    # @sync_to_async
    # def mark_meeting_as_scheduled(meeting_id: int):
    #     """Помечает встречу, что для нее запланированы задачи."""
    #     SecretCoffeeMeeting.objects.filter(id=meeting_id).update(
    #         scheduling_status='scheduled'
    #     )
    #     logger.info(f"Встреча {meeting_id} помечена как 'запланированная'.")

    @staticmethod
    @sync_to_async
    def get_meeting_by_id(meeting_id: int):
        """Получает встречу по ID."""
        try:
            return SecretCoffeeMeeting.objects.get(id=meeting_id)
        except SecretCoffeeMeeting.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async
    def get_meeting_participant_ids(meeting_id: int):
        """Получает Telegram ID участников встречи."""
        meeting = SecretCoffeeMeeting.objects.get(id=meeting_id)
        return [meeting.employee1.telegram_id, meeting.employee2.telegram_id]


# Создаем единый экземпляр сервиса для использования в других частях приложения
feedback_service = FeedbackService()
