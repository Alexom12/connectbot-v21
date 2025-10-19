import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from employees.models import Employee
from activities.models import SecretCoffeeMeeting, ActivitySession

class Command(BaseCommand):
    """
    Создает тестовые данные для проверки отправки уведомлений.
    - Создает двух сотрудников (если их нет).
    - Создает сессию 'Тайного кофе'.
    - Создает завершенную встречу между ними без дедлайна.
    """
    help = 'Creates a completed meeting for testing notifications.'

    def handle(self, *args, **options):
        self.stdout.write("Создание тестовых данных...")

        # --- 1. Создание сотрудников ---
        employee1, created1 = Employee.objects.get_or_create(
            telegram_id=987654321,  # Используйте тестовый ID
            defaults={
                'full_name': 'Тестовый Пользователь 1',
                'email': 'test1@example.com',
            }
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f"Создан сотрудник: {employee1.full_name}"))
        
        employee2, created2 = Employee.objects.get_or_create(
            telegram_id=123456789,  # Используйте ваш реальный ID для получения уведомления
            defaults={
                'full_name': 'Настоящий Пользователь',
                'email': 'realuser@example.com',
            }
        )
        if created2:
            self.stdout.write(self.style.SUCCESS(f"Создан сотрудник: {employee2.full_name}"))
        else:
             self.stdout.write(f"Сотрудник {employee2.full_name} уже существует. Убедитесь, что его telegram_id={employee2.telegram_id} верный для теста.")


        # --- 2. Создание сессии ---
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        session, created_session = ActivitySession.objects.get_or_create(
            activity_type='secret_coffee',
            week_start=week_start,
            defaults={'status': 'completed'}
        )
        if created_session:
            self.stdout.write(self.style.SUCCESS(f"Создана сессия: {session}"))

        # --- 3. Создание завершенной встречи ---
        meeting_id = f"test_meeting_{random.randint(1000, 9999)}"
        meeting, created_meeting = SecretCoffeeMeeting.objects.get_or_create(
            meeting_id=meeting_id,
            defaults={
                'activity_session': session,
                'employee1': employee1,
                'employee2': employee2,
                'status': 'completed',
                'meeting_format': 'OFFLINE',
                'feedback_deadline': None, # Важно для теста
            }
        )

        if created_meeting:
            self.stdout.write(self.style.SUCCESS(f"Создана тестовая встреча: ID {meeting.meeting_id}"))
        else:
            # Если встреча уже есть, убедимся, что она подходит для теста
            meeting.status = 'completed'
            meeting.feedback_deadline = None
            meeting.save()
            self.stdout.write(self.style.WARNING(f"Встреча {meeting.meeting_id} уже существовала. Обновлен статус и сброшен дедлайн."))

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы/обновлены."))
        self.stdout.write(f"Чтобы запустить проверку, выполните: python manage.py schedule_feedback")
