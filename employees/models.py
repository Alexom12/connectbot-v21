"""
Модели для модуля сотрудников
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    """Модель отдела/департамента"""
    name = models.CharField("Название отдела", max_length=200, unique=True)
    code = models.CharField("Код отдела", max_length=50, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активный", default=True)
    
    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BusinessCenter(models.Model):
    """Модель бизнес-центра"""
    name = models.CharField("Название БЦ", max_length=200, unique=True)
    address = models.TextField("Адрес", blank=True)
    is_active = models.BooleanField("Активный", default=True)
    
    class Meta:
        verbose_name = "Бизнес-центр"
        verbose_name_plural = "Бизнес-центры"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Employee(models.Model):
    """Модель сотрудника"""
    
    # Основная информация
    full_name = models.CharField("ФИО", max_length=200)
    position = models.CharField("Должность", max_length=200, blank=True, null=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        verbose_name="Отдел", 
        blank=True, 
        null=True
    )
    business_center = models.ForeignKey(
        BusinessCenter,
        on_delete=models.SET_NULL,
        verbose_name="Бизнес-центр", 
        blank=True, 
        null=True
    )
    
    # Telegram данные
    telegram_id = models.BigIntegerField("Telegram ID", unique=True, blank=True, null=True)
    telegram_username = models.CharField("Telegram username", max_length=100, blank=True, null=True)
    normalized_username = models.CharField("Нормализованный username", max_length=100, blank=True, null=True)
    
    # Контактная информация
    email = models.EmailField("Email", blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    
    # Дополнительная информация
    birth_date = models.DateField("Дата рождения", blank=True, null=True)
    hire_date = models.DateField("Дата приема на работу", blank=True, null=True)
    is_active = models.BooleanField("Активный", default=True)
    
    # Системные поля
    authorized = models.BooleanField("Авторизован", default=False)
    last_activity = models.DateTimeField("Последняя активность", blank=True, null=True)
    
    # Даты
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['telegram_username']),
            models.Index(fields=['normalized_username']),
            models.Index(fields=['is_active', 'authorized']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.position or 'Нет должности'})"
    
    def save(self, *args, **kwargs):
        """Переопределяем save для нормализации username"""
        if self.telegram_username:
            self.normalized_username = self.normalize_username(self.telegram_username)
        super().save(*args, **kwargs)
    
    @staticmethod
    def normalize_username(username):
        """Нормализация username для поиска"""
        if not username:
            return ""
        return username.strip().lstrip('@').lower().replace('_', '').replace('-', '').replace('.', '')
    
    def get_interests_list(self):
        """Получить список активных интересов сотрудника"""
        return [ei.interest for ei in self.interests.filter(is_active=True)]
    
    def get_activity_stats(self):
        """Получить статистику активностей сотрудника"""
        from django.db.models import Count
        return self.activities.values('activity_type').annotate(count=Count('id'))
    
    @classmethod
    def find_by_telegram_data(cls, telegram_user):
        """
        Поиск сотрудника по данным Telegram пользователя
        с использованием relaxed matching
        """
        if not telegram_user:
            return None
        
        username = getattr(telegram_user, 'username', None)
        user_id = getattr(telegram_user, 'id', None)
        
        # Сначала пробуем найти по telegram_id (самый надежный способ)
        if user_id:
            try:
                employee = cls.objects.filter(telegram_id=user_id, is_active=True).first()
                if employee:
                    return employee
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка поиска по telegram_id {user_id}: {e}")
        
        # Поиск по username
        return cls.find_by_username(username)
    
    @classmethod
    def find_by_username(cls, username):
        """
        Поиск сотрудника по username с relaxed matching
        """
        if not username:
            return None
        
        normalized_username = cls.normalize_username(username)
        
        try:
            # 1. Точный поиск по telegram_username
            employees = cls.objects.filter(
                telegram_username__iexact=username,
                is_active=True
            )
            
            if employees.count() == 1:
                return employees.first()
            
            # 2. Поиск по normalized_username
            employees = cls.objects.filter(
                normalized_username=normalized_username,
                is_active=True
            )
            
            if employees.count() == 1:
                return employees.first()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка поиска сотрудника по username {username}: {e}")
        
        return None
    
    def update_telegram_data(self, telegram_user):
        """
        Обновление Telegram данных сотрудника
        """
        updated = False
        
        if hasattr(telegram_user, 'username') and telegram_user.username and not self.telegram_username:
            self.telegram_username = telegram_user.username
            updated = True
        
        if hasattr(telegram_user, 'id') and telegram_user.id and not self.telegram_id:
            # Проверяем, что telegram_id уникален
            existing = Employee.objects.filter(telegram_id=telegram_user.id).exclude(pk=self.pk).first()
            if not existing:
                self.telegram_id = telegram_user.id
                updated = True
        
        if updated:
            self.save(update_fields=['telegram_id', 'telegram_username'])
            return True
        
        return False


class Interest(models.Model):
    """Модель интересов/активностей"""
    
    INTEREST_TYPES = [
        ('coffee', '☕️ Тайный кофе'),
        ('lunch', '🍝 Обед вслепую'), 
        ('walk', '🚶 Слепая прогулка'),
        ('chess', '♟️ Шахматы'),
        ('pingpong', '🏓 Настольный теннис'),
        ('games', '🎲 Настольные игры'),
        ('photo', '📸 Фотоквесты'),
        ('masterclass', '🧠 Мастер-классы'),
        ('clubs', '📚 Клубы по интересам'),
    ]
    
    code = models.CharField("Код", max_length=20, choices=INTEREST_TYPES, unique=True)
    name = models.CharField("Название", max_length=100)
    emoji = models.CharField("Эмодзи", max_length=10)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активный", default=True)
    
    # Настройки активности
    auto_schedule = models.BooleanField("Авто-планирование", default=True)
    schedule_frequency = models.CharField(
        "Частота", 
        max_length=20, 
        choices=[
            ('weekly', 'Еженедельно'),
            ('biweekly', 'Раз в две недели'), 
            ('monthly', 'Ежемесячно'),
        ],
        default='weekly'
    )
    
    class Meta:
        verbose_name = "Интерес"
        verbose_name_plural = "Интересы"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.emoji} {self.name}"
    
    def get_active_subscribers_count(self):
        """Количество активных подписчиков"""
        return self.employeeinterest_set.filter(is_active=True).count()


class EmployeeInterest(models.Model):
    """Связь сотрудника с интересами"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    is_active = models.BooleanField("Активна", default=True)
    
    # Настройки уведомлений
    receive_notifications = models.BooleanField("Получать уведомления", default=True)
    notification_frequency = models.CharField(
        "Частота уведомлений",
        max_length=20,
        choices=[
            ('immediate', 'Мгновенно'),
            ('daily', 'Ежедневно'),
            ('weekly', 'Еженедельно'),
        ],
        default='immediate'
    )
    
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)
    
    class Meta:
        verbose_name = "Интерес сотрудника"
        verbose_name_plural = "Интересы сотрудников"
        unique_together = ['employee', 'interest']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['interest', 'is_active']),
        ]
    
    def __str__(self):
        status = "✅" if self.is_active else "❌"
        return f"{status} {self.employee.full_name} - {self.interest.name}"


class Activity(models.Model):
    """Модель активности/мероприятия"""
    
    ACTIVITY_TYPES = [
        ('coffee', 'Тайный кофе'),
        ('lunch', 'Обед вслепую'),
        ('walk', 'Слепая прогулка'), 
        ('chess', 'Шахматы'),
        ('pingpong', 'Настольный теннис'),
        ('games', 'Настольные игры'),
        ('photo', 'Фотоквест'),
        ('masterclass', 'Мастер-класс'),
        ('club', 'Клуб по интересам'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('scheduled', 'Запланировано'),
        ('active', 'Активно'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    # Основная информация
    title = models.CharField("Название", max_length=200)
    activity_type = models.CharField("Тип активности", max_length=20, choices=ACTIVITY_TYPES)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE, verbose_name="Интерес")
    description = models.TextField("Описание", blank=True)
    
    # Время проведения
    scheduled_date = models.DateField("Дата проведения")
    scheduled_time = models.TimeField("Время проведения", blank=True, null=True)
    duration_minutes = models.IntegerField("Длительность (минут)", default=30)
    
    # Статус
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='draft')
    max_participants = models.IntegerField("Максимум участников", default=2)
    
    # Системные поля
    is_auto_created = models.BooleanField("Авто-создано", default=False)
    created_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        verbose_name="Создано",
        blank=True, 
        null=True,
        related_name='created_activities'
    )
    
    # Даты
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    
    class Meta:
        verbose_name = "Активность"
        verbose_name_plural = "Активности"
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['activity_type', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['interest', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.title} ({self.scheduled_date})"
    
    def get_participants_count(self):
        """Количество подтвердивших участников"""
        return self.participants.filter(status='confirmed').count()
    
    def is_fully_booked(self):
        """Проверка, заполнена ли активность"""
        return self.get_participants_count() >= self.max_participants
    
    def can_join(self):
        """Можно ли присоединиться к активности"""
        return (self.status in ['scheduled', 'active'] and 
                not self.is_fully_booked())


class ActivityParticipant(models.Model):
    """Участники активности"""
    
    STATUS_CHOICES = [
        ('invited', 'Приглашен'),
        ('confirmed', 'Подтвердил'),
        ('declined', 'Отказался'),
        ('attended', 'Присутствовал'),
        ('no_show', 'Не явился'),
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='participants')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='activities')
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='invited')
    
    # Обратная связь
    rating = models.IntegerField(
        "Оценка", 
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback = models.TextField("Отзыв", blank=True)
    
    # Даты
    invited_at = models.DateTimeField("Приглашен", auto_now_add=True)
    responded_at = models.DateTimeField("Ответил", blank=True, null=True)
    attended_at = models.DateTimeField("Присутствовал", blank=True, null=True)
    
    class Meta:
        verbose_name = "Участник активности"
        verbose_name_plural = "Участники активностей"
        unique_together = ['activity', 'employee']
        indexes = [
            models.Index(fields=['activity', 'status']),
            models.Index(fields=['employee', 'status']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.activity.title} ({self.get_status_display()})"


class Achievement(models.Model):
    """Модель достижений"""
    
    ACHIEVEMENT_TYPES = [
        ('participation', 'Участие'),
        ('consistency', 'Постоянство'),
        ('social', 'Социальная активность'),
        ('expert', 'Экспертность'),
        ('special', 'Особое достижение'),
    ]
    
    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    achievement_type = models.CharField("Тип достижения", max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField("Иконка", max_length=50, default="🏆")
    
    # Условия получения
    condition_type = models.CharField(
        "Тип условия",
        max_length=20,
        choices=[
            ('count', 'Количество участий'),
            ('streak', 'Серия участий'),
            ('variety', 'Разнообразие активностей'),
            ('manual', 'Ручное назначение'),
        ]
    )
    condition_value = models.IntegerField("Значение условия", default=1)
    condition_activity_type = models.CharField(
        "Тип активности для условия", 
        max_length=20, 
        blank=True, 
        null=True
    )
    
    # Награда
    points_reward = models.IntegerField("Награда в баллах", default=10)
    
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    
    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ['achievement_type', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class EmployeeAchievement(models.Model):
    """Достижения сотрудников"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField("Получено", auto_now_add=True)
    progress = models.FloatField("Прогресс", default=0.0)
    
    class Meta:
        verbose_name = "Достижение сотрудника"
        verbose_name_plural = "Достижения сотрудников"
        unique_together = ['employee', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.achievement.name}"


class BotAdmin(models.Model):
    """Модель администраторов бота"""
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bot_admin')
    is_super_admin = models.BooleanField("Супер-администратор", default=False)
    can_manage_users = models.BooleanField("Может управлять пользователями", default=True)
    can_manage_activities = models.BooleanField("Может управлять активностями", default=True)
    can_view_reports = models.BooleanField("Может просматривать отчеты", default=True)
    
    added_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        related_name='added_admins',
        blank=True, 
        null=True
    )
    added_at = models.DateTimeField("Добавлен", auto_now_add=True)
    
    class Meta:
        verbose_name = "Администратор бота"
        verbose_name_plural = "Администраторы бота"
    
    def __str__(self):
        admin_type = "🤴 Супер-админ" if self.is_super_admin else "👨💼 Админ"
        return f"{admin_type}: {self.employee.full_name}"