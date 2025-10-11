from django.db import models
from employees.models import Employee

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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'secret_coffee_meetings'
        indexes = [
            models.Index(fields=['meeting_id']),
            models.Index(fields=['status']),
            models.Index(fields=['meeting_date']),
        ]

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