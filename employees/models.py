"""
Модели для модуля сотрудников
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.html import format_html
from .redis_utils import RedisManager
import logging

logger = logging.getLogger(__name__)


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
        """Переопределяем save для нормализации username и очистки кеша"""
        if self.telegram_username:
            self.normalized_username = self.normalize_username(self.telegram_username)
        
        super().save(*args, **kwargs)
        
        # Очищаем кеш при изменении данных сотрудника
        if self.telegram_id:
            RedisManager.invalidate_employee_cache(self.telegram_id)
    
    @staticmethod
    def normalize_username(username):
        """Нормализация username для поиска"""
        if not username:
            return ""
        return username.strip().lstrip('@').lower().replace('_', '').replace('-', '').replace('.', '')
    
    def get_interests_list(self):
        """Получить список активных интересов сотрудника с кешированием"""
        # Пытаемся получить из кеша
        interests = RedisManager.get_employee_interests(self.id)
        if interests is not None:
            return interests
        
        # Загружаем из БД и кешируем
        interests = [ei.interest for ei in self.interests.filter(is_active=True)]
        RedisManager.cache_employee_interests(self.id, interests)
        return interests
    
    def get_activity_stats(self):
        """Получить статистику активностей сотрудника"""
        from django.db.models import Count
        return self.activities.values('activity_type').annotate(count=Count('id'))
    
    @classmethod
    def find_by_telegram_data(cls, telegram_user):
        """
        Поиск сотрудника по данным Telegram пользователя
        с использованием relaxed matching и кеширования
        """
        if not telegram_user:
            return None
        
        username = getattr(telegram_user, 'username', None)
        user_id = getattr(telegram_user, 'id', None)
        
        # Сначала пробуем найти по telegram_id (самый надежный способ)
        if user_id:
            try:
                # Проверяем кеш сначала
                employee_data = RedisManager.get_employee_data(user_id)
                if employee_data:
                    return cls.objects.get(id=employee_data['id'])
                
                employee = cls.objects.filter(telegram_id=user_id, is_active=True).first()
                if employee:
                    # Кешируем найденного сотрудника
                    RedisManager.cache_employee_data(
                        user_id, 
                        {
                            'id': employee.id,
                            'full_name': employee.full_name,
                            'position': employee.position,
                            'telegram_id': employee.telegram_id,
                            'telegram_username': employee.telegram_username,
                        }
                    )
                    return employee
            except Exception as e:
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
        """Количество подтвердивших участников с кешированием"""
        # Пытаемся получить из кеша
        participants = RedisManager.get_activity_participants(self.id)
        if participants is not None:
            return len([p for p in participants if p.get('status') == 'confirmed'])
        
        # Загружаем из БД и кешируем
        participants_data = []
        for p in self.participants.all():
            participants_data.append({
                'id': p.id,
                'employee_id': p.employee.id,
                'employee_name': p.employee.full_name,
                'status': p.status
            })
        
        RedisManager.cache_activity_participants(self.id, participants_data)
        return len([p for p in participants_data if p.get('status') == 'confirmed'])
    
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


# === СИСТЕМА АДМИНИСТРАТОРОВ ===

class AdminUser(models.Model):
    """Модель администраторов системы"""
    ROLE_CHOICES = [
        ('superadmin', 'Супер администратор'),
        ('admin', 'Администратор'),
        ('moderator', 'Модератор'),
    ]
    
    user = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='moderator')
    permissions = models.JSONField("Права доступа", default=list, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        db_table = 'admin_users'
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} ({self.role})"

    def has_permission(self, permission):
        """Проверка прав доступа"""
        if self.role == 'superadmin':
            return True
        return permission in self.permissions

    def get_role_display_with_emoji(self):
        """Отображение роли с эмодзи"""
        emoji_map = {
            'superadmin': '👑',
            'admin': '🔧', 
            'moderator': '👁️'
        }
        emoji = emoji_map.get(self.role, '👤')
        return f"{emoji} {self.get_role_display()}"


class AdminLog(models.Model):
    """Модель логов действий администраторов"""
    ACTION_CHOICES = [
        ('login', 'Вход в систему'),
        ('command', 'Выполнение команды'),
        ('manage', 'Управление объектом'),
        ('system', 'Системное действие'),
        ('error', 'Ошибка'),
    ]
    
    admin = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='logs', verbose_name="Администратор")
    action = models.CharField("Действие", max_length=50, choices=ACTION_CHOICES)
    command = models.CharField("Команда", max_length=100, blank=True)
    target_type = models.CharField("Тип объекта", max_length=50, blank=True)
    target_id = models.IntegerField("ID объекта", null=True, blank=True)
    details = models.JSONField("Детали", default=dict)
    ip_address = models.GenericIPAddressField("IP адрес", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        db_table = 'admin_logs'
        verbose_name = 'Лог администратора'
        verbose_name_plural = 'Логи администраторов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"{self.admin.user.full_name} - {self.action} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    def get_action_display_with_emoji(self):
        """Отображение действия с эмодзи"""
        emoji_map = {
            'login': '🔐',
            'command': '⌨️',
            'manage': '⚙️',
            'system': '🖥️',
            'error': '❌'
        }
        emoji = emoji_map.get(self.action, '📝')
        return f"{emoji} {self.get_action_display()}"


# === Система "Тайный кофе" ===

class SecretCoffee(models.Model):
    """Еженедельная сессия тайного кофе"""
    
    week_start = models.DateField("Начало недели", help_text="Понедельник недели, для которой создаются пары")
    title = models.CharField("Название сессии", max_length=200, blank=True)
    description = models.TextField("Описание", blank=True)
    
    # Статус сессии
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('active', 'Активная'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Настройки создания пар
    max_pairs = models.IntegerField("Максимум пар", default=50, help_text="Максимальное количество пар для сессии")
    algorithm_used = models.CharField(
        "Использованный алгоритм", 
        max_length=50, 
        blank=True,
        help_text="Алгоритм, использованный для создания пар"
    )
    
    # Временные рамки
    registration_deadline = models.DateTimeField("Дедлайн регистрации", blank=True, null=True)
    meeting_deadline = models.DateField("Дедлайн встреч", blank=True, null=True)
    
    # Статистика
    total_participants = models.IntegerField("Всего участников", default=0)
    successful_pairs = models.IntegerField("Успешных пар", default=0)
    
    # Системные поля
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        verbose_name="Создано",
        blank=True,
        null=True,
        related_name='created_coffee_sessions'
    )
    
    class Meta:
        verbose_name = "Сессия тайного кофе"
        verbose_name_plural = "Сессии тайного кофе"
        ordering = ['-week_start']
        unique_together = ['week_start']  # Одна сессия на неделю
        indexes = [
            models.Index(fields=['week_start', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        title = self.title or f"Тайный кофе на неделю {self.week_start.strftime('%d.%m.%Y')}"
        return f"{title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        """Автоматически создаем название если не указано"""
        if not self.title:
            self.title = f"Тайный кофе на неделю {self.week_start.strftime('%d.%m.%Y')}"
        super().save(*args, **kwargs)
    
    def get_pairs_count(self):
        """Количество созданных пар"""
        return self.coffee_pairs.count()
    
    def get_confirmed_pairs_count(self):
        """Количество подтвержденных пар (обе стороны подтвердили)"""
        return self.coffee_pairs.filter(
            confirmed_employee1=True,
            confirmed_employee2=True
        ).count()
    
    def get_participation_rate(self):
        """Процент участия (отношение подтвержденных к общему числу)"""
        total = self.get_pairs_count()
        if total == 0:
            return 0
        confirmed = self.get_confirmed_pairs_count()
        return round((confirmed / total) * 100, 1)


class CoffeePair(models.Model):
    """Пара сотрудников для тайного кофе"""
    
    secret_coffee = models.ForeignKey(
        SecretCoffee, 
        on_delete=models.CASCADE, 
        related_name='coffee_pairs',
        verbose_name="Сессия тайного кофе"
    )
    employee1 = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='coffee_pairs_as_first',
        verbose_name="Первый сотрудник"
    )
    employee2 = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='coffee_pairs_as_second',
        verbose_name="Второй сотрудник"
    )
    
    # Подтверждения участников
    confirmed_employee1 = models.BooleanField("Подтверждение от первого", default=False)
    confirmed_employee2 = models.BooleanField("Подтверждение от второго", default=False)
    
    # Чат и коммуникация
    chat_created = models.BooleanField("Чат создан", default=False)
    chat_id = models.BigIntegerField("ID чата", blank=True, null=True)
    
    # Информация о встрече
    meeting_scheduled = models.BooleanField("Встреча запланирована", default=False)
    meeting_date = models.DateTimeField("Дата встречи", blank=True, null=True)
    meeting_place = models.CharField("Место встречи", max_length=200, blank=True)
    meeting_completed = models.BooleanField("Встреча состоялась", default=False)
    
    # Обратная связь
    feedback_employee1 = models.TextField("Отзыв первого сотрудника", blank=True)
    feedback_employee2 = models.TextField("Отзыв второго сотрудника", blank=True)
    rating_employee1 = models.IntegerField(
        "Оценка от первого", 
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка от 1 до 5"
    )
    rating_employee2 = models.IntegerField(
        "Оценка от второго", 
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка от 1 до 5"
    )
    
    # Алгоритм matching
    match_score = models.FloatField("Оценка совместимости", default=0.0, help_text="Оценка алгоритма от 0 до 1")
    match_reason = models.TextField("Причина объединения в пару", blank=True)
    
    # Статус пары
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('notified', 'Уведомления отправлены'),
        ('confirmed', 'Подтверждена'),
        ('meeting_scheduled', 'Встреча запланирована'),
        ('completed', 'Завершена'),
        ('declined', 'Отказались'),
        ('expired', 'Просрочена'),
    ]
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='created')
    
    # Временные метки
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    notified_at = models.DateTimeField("Уведомления отправлены", blank=True, null=True)
    confirmed_at = models.DateTimeField("Подтверждено", blank=True, null=True)
    completed_at = models.DateTimeField("Завершено", blank=True, null=True)
    
    class Meta:
        verbose_name = "Пара для тайного кофе"
        verbose_name_plural = "Пары для тайного кофе"
        ordering = ['-created_at']
        unique_together = [
            ['secret_coffee', 'employee1', 'employee2']  # Уникальная пара в рамках сессии
        ]
        indexes = [
            models.Index(fields=['secret_coffee', 'status']),
            models.Index(fields=['employee1', 'status']),
            models.Index(fields=['employee2', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.employee1.full_name} ↔ {self.employee2.full_name} ({self.secret_coffee.week_start})"
    
    def save(self, *args, **kwargs):
        """Валидация и обновление статусов при сохранении"""
        # Проверяем, что сотрудники разные
        if self.employee1_id == self.employee2_id:
            raise ValueError("Сотрудник не может быть в паре с самим собой")
        
        # Обновляем статус на основе подтверждений
        if self.confirmed_employee1 and self.confirmed_employee2 and self.status == 'notified':
            self.status = 'confirmed'
            self.confirmed_at = models.functions.Now()
        
        super().save(*args, **kwargs)
    
    def is_fully_confirmed(self):
        """Проверка, подтвердили ли оба участника"""
        return self.confirmed_employee1 and self.confirmed_employee2
    
    def has_feedback_from_both(self):
        """Проверка, оставили ли оба участника обратную связь"""
        return bool(self.feedback_employee1) and bool(self.feedback_employee2)
    
    def get_average_rating(self):
        """Средняя оценка от обоих участников"""
        ratings = [r for r in [self.rating_employee1, self.rating_employee2] if r is not None]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)
    
    def get_other_employee(self, current_employee):
        """Получить второго сотрудника в паре"""
        if current_employee.id == self.employee1_id:
            return self.employee2
        elif current_employee.id == self.employee2_id:
            return self.employee1
        return None
    
    def can_be_confirmed_by(self, employee):
        """Может ли сотрудник подтвердить участие в паре"""
        if employee.id == self.employee1_id:
            return not self.confirmed_employee1
        elif employee.id == self.employee2_id:
            return not self.confirmed_employee2
        return False
    
    def confirm_by_employee(self, employee):
        """Подтверждение участия от конкретного сотрудника"""
        if employee.id == self.employee1_id and not self.confirmed_employee1:
            self.confirmed_employee1 = True
            self.save()
            return True
        elif employee.id == self.employee2_id and not self.confirmed_employee2:
            self.confirmed_employee2 = True
            self.save()
            return True
        return False