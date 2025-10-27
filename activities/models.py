from django.db import models
from employees.models import Employee
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from asgiref.sync import sync_to_async

# Типы активностей
ACTIVITY_TYPES = [
    ('secret_coffee', 'Тайный кофе'),
    ('chess', 'Шахматы'), 
    ('ping_pong', 'Настольный теннис'),
    ('photo_quest', 'Фотоквест'),
    ('workshop', 'Мастер-класс'),
]

# Статусы сессий
SESSION_STATUS = [
    ('planned', 'Запланирована'),
    ('active', 'Активна'),
    ('completed', 'Завершена'),
    ('cancelled', 'Отменена'),
]

class ActivitySession(models.Model):
    """Сессия активности (еженедельная)"""
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    week_start = models.DateField()
    status = models.CharField(max_length=15, choices=SESSION_STATUS, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_sessions'
        unique_together = ['activity_type', 'week_start']
        indexes = [
            models.Index(fields=['activity_type', 'week_start']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.week_start}"

class ActivityParticipant(models.Model):
    """Участники активностей"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='activity_participations')
    activity_session = models.ForeignKey(ActivitySession, on_delete=models.CASCADE, related_name='participants')
    subscription_status = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_participants'
        unique_together = ['employee', 'activity_session']
        indexes = [
            models.Index(fields=['employee', 'subscription_status']),
            models.Index(fields=['activity_session', 'subscription_status']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.activity_session}"

class ActivityPair(models.Model):
    """Пары/команды для активностей"""
    activity_session = models.ForeignKey(ActivitySession, on_delete=models.CASCADE, related_name='pairs')
    employee1 = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pair1_activities')
    employee2 = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='pair2_activities')
    chat_created = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_pairs'
        unique_together = ['activity_session', 'employee1', 'employee2']
        indexes = [
            models.Index(fields=['activity_session', 'chat_created']),
        ]
    
    def __str__(self):
        return f"{self.employee1.name} & {self.employee2.name} - {self.activity_session}"
    # Добавляем к существующим моделям
class SecretCoffeeMeeting(models.Model):
    """Модель для анонимной встречи Тайного кофе"""
    meeting_id = models.CharField(max_length=20, unique=True)
    activity_session = models.ForeignKey(ActivitySession, on_delete=models.CASCADE)
    employee1 = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='secret_coffee_initiator')
    employee2 = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='secret_coffee_partner')
    
    # Статусы встречи
    STATUS_CHOICES = [
        ('planned', 'Запланирована'),
        ('scheduling', 'В процессе планирования'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
        ('failed', 'Не состоялась'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planned')
    
    # Данные встречи (заполняются после подтверждения)
    meeting_date = models.DateTimeField(null=True, blank=True)
    meeting_location = models.CharField(max_length=100, blank=True)
    meeting_format = models.CharField(max_length=10, choices=[('ONLINE', 'Онлайн'), ('OFFLINE', 'Оффлайн')])
    
    # Анонимные идентификаторы
    employee1_code = models.CharField(max_length=20)  # Код для employee1
    employee2_code = models.CharField(max_length=20)  # Код для employee2
    recognition_sign = models.CharField(max_length=50, blank=True)  # Опознавательный знак
    
    # Безопасность
    emergency_stopped = models.BooleanField(default=False)
    moderator_notified = models.BooleanField(default=False)
    
    # Поля для системы отзывов
    feedback_collected = models.BooleanField("Сбор отзывов завершен", default=False)
    average_rating = models.FloatField("Средний рейтинг", null=True, blank=True)
    feedback_deadline = models.DateTimeField("Дедлайн для отзывов", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'secret_coffee_meetings'
        indexes = [
            models.Index(fields=['meeting_id']),
            models.Index(fields=['status']),
            models.Index(fields=['meeting_date']),
        ]

    @sync_to_async
    def get_partner(self, current_user_telegram_id: int):
        """Возвращает партнера по встрече."""
        if self.employee1.telegram_id == current_user_telegram_id:
            return self.employee2
        elif self.employee2.telegram_id == current_user_telegram_id:
            return self.employee1
        return None

    # Оборачиваем синхронный метод get_partner в асинхронную версию
    aget_partner = get_partner

    def mark_feedback_collected(self):
        """Отметить, что сбор отзывов по этой встрече завершен."""
        self.feedback_collected = True
        self.save(update_fields=['feedback_collected'])

    def calculate_average_rating(self):
        """Рассчитать и сохранить средний рейтинг по всем отзывам."""
        avg_rating = self.feedbacks.aggregate(models.Avg('rating'))['rating__avg']
        if avg_rating is not None:
            self.average_rating = round(avg_rating, 2)
            self.save(update_fields=['average_rating'])
        return self.average_rating

    def get_feedback_status(self):
        """Получить статус сбора отзывов (например, 'pending', 'completed', 'overdue')."""
        if self.feedback_collected:
            return 'completed'
        if self.feedback_deadline and timezone.now() > self.feedback_deadline:
            return 'overdue'
        return 'pending'

class SecretCoffeePreference(models.Model):
    """Предпочтения сотрудника для Тайного кофе"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='coffee_preferences')
    
    # Доступность
    availability_slots = models.JSONField(default=list)  # ['mon_10-12', 'tue_14-16', ...]
    
    # Форматы
    PREFERRED_FORMATS = [
        ('ONLINE', 'Только онлайн'),
        ('OFFLINE', 'Только оффлайн'),
        ('BOTH', 'Оба формата'),
    ]
    preferred_format = models.CharField(max_length=10, choices=PREFERRED_FORMATS, default='BOTH')
    
    # Локация (для оффлайн)
    office_location = models.CharField(max_length=50, blank=True)
    
    # Интересы для разговора
    topics_of_interest = models.JSONField(default=list)
    
    # Исключения (опционально)
    avoid_specific_people = models.JSONField(default=list)  # IDs сотрудников
    
    # Настройки анонимности
    allow_photo_sharing = models.BooleanField(default=False)
    emergency_contact = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'secret_coffee_preferences'

class SecretCoffeeMessage(models.Model):
    """Сообщения между участниками через бота-посредника"""
    meeting = models.ForeignKey(SecretCoffeeMeeting, on_delete=models.CASCADE, related_name='messages')
    from_employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=[
        ('text', 'Текст'),
        ('proposal', 'Предложение встречи'),
        ('confirmation', 'Подтверждение'),
        ('photo', 'Фото'),
        ('emergency', 'Экстренное сообщение'),
    ])
    content = models.TextField()
    is_forwarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'secret_coffee_messages'
        indexes = [
            models.Index(fields=['meeting', 'created_at']),
        ]

class SecretCoffeeProposal(models.Model):
    """Предложения по времени/месту встречи"""
    meeting = models.ForeignKey(SecretCoffeeMeeting, on_delete=models.CASCADE, related_name='proposals')
    from_employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    proposed_date = models.DateTimeField()
    proposed_location = models.CharField(max_length=100)
    proposed_format = models.CharField(max_length=10, choices=[('ONLINE', 'Онлайн'), ('OFFLINE', 'Оффлайн')])
    
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
        ('countered', 'Предложен встречный вариант'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'secret_coffee_proposals'

class MeetingFeedback(models.Model):
    """Модель для сбора отзывов о встречах"""
    
    FEEDBACK_TYPES = [
        ('coffee', 'Тайный кофе'),
        ('chess', 'Шахматы'),
        ('pingpong', 'Настольный теннис'),
        ('workshop', 'Мастер-класс'),
        ('photo_quest', 'Фотоквест'),
    ]

    meeting = models.ForeignKey(
        SecretCoffeeMeeting, 
        on_delete=models.CASCADE, 
        related_name='feedbacks',
        verbose_name='Встреча'
    )
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='given_feedbacks',
        verbose_name='Сотрудник'
    )
    rating = models.IntegerField(
        "Рейтинг",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка от 1 до 5"
    )
    anonymous_feedback = models.TextField("Анонимный отзыв", blank=True)
    suggestions = models.TextField("Предложения", blank=True)
    feedback_type = models.CharField(
        "Тип отзыва", 
        max_length=20, 
        choices=FEEDBACK_TYPES,
        default='coffee'
    )
    is_anonymous = models.BooleanField("Анонимно", default=True)
    created_at = models.DateTimeField("Дата отзыва", auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.employee.full_name if not self.is_anonymous else 'Аноним'} на встречу {self.meeting.meeting_id}"

    def calculate_impact_score(self):
        """
        Расчёт влияния отзыва.
        Например, низкая оценка имеет большее влияние.
        """
        return (5 - self.rating) * 0.5 + len(self.anonymous_feedback) * 0.01

    class Meta:
        unique_together = ['meeting', 'employee']
        verbose_name = 'Отзыв о встрече'
        verbose_name_plural = 'Отзывы о встречах'
        db_table = 'meeting_feedback'
        ordering = ['-created_at']


# ------------------------------------------------------------
# Backwards-compatible aliases
# ------------------------------------------------------------
# Historically `Activity` and related models lived in this module.
# They were refactored to `employees.models`. Some modules still
# import `Activity` / `ActivityParticipant` and `Meeting` from
# `activities.models`. Provide compatibility aliases to avoid
# ImportError while keeping a single canonical definition.
try:
    from employees.models import Activity as Activity
    from employees.models import ActivityParticipant as ActivityParticipant
except Exception:
    # If import fails for any reason (e.g., circular import during
    # migrations), leave names as None so the original ImportError
    # surfaces in a clear way.
    Activity = None
    ActivityParticipant = None

# Many modules referred to a `Meeting` model; map it to the secret
# coffee meeting model used in this app to preserve behaviour.
Meeting = SecretCoffeeMeeting

__all__ = [
    'ActivitySession', 'ActivityParticipant', 'ActivityPair',
    'SecretCoffeeMeeting', 'SecretCoffeePreference', 'SecretCoffeeMessage',
    'SecretCoffeeProposal', 'MeetingFeedback',
    'Activity', 'ActivityParticipant', 'Meeting'
]