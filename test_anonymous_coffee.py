import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

async def test_anonymous_coffee():
    print("🧪 Тестирование анонимного Тайного кофе...")
    
    from activities.services.anonymous_coffee_service import anonymous_coffee_service
    from activities.models import ActivitySession, ActivityParticipant
    from employees.models import Employee
    from django.utils import timezone
    from datetime import timedelta
    
    # Получаем тестовых сотрудников
    from asgiref.sync import sync_to_async
    employees = await sync_to_async(list)(Employee.objects.all()[:4])
    
    if len(employees) < 2:
        print("❌ Недостаточно сотрудников для теста")
        return
    
    # Создаем тестовую сессию если её нет
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    session, created = await sync_to_async(ActivitySession.objects.get_or_create)(
        activity_type='secret_coffee',
        week_start=week_start,
        defaults={'status': 'planned'}
    )
    
    print(f"📋 Сессия secret_coffee: {'создана' if created else 'существует'}")
    
    # Добавляем участников в сессию
    for i, employee in enumerate(employees[:4]):  # Берем максимум 4 сотрудников
        participant, created = await sync_to_async(ActivityParticipant.objects.get_or_create)(
            employee=employee,
            activity_session=session,
            defaults={'subscription_status': True}
        )
        if created:
            print(f"   + {employee.full_name} добавлен как участник")
    
    print(f"1. Тестирование matching для {len(employees)} сотрудников...")
    success = await anonymous_coffee_service.run_weekly_matching()
    print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
    
    print("2. Проверка создания встреч...")
    from activities.models import SecretCoffeeMeeting
    try:
        meetings_count = await sync_to_async(SecretCoffeeMeeting.objects.count)()
        print(f"   Создано встреч: {meetings_count}")
        
        if meetings_count > 0:
            meetings = await sync_to_async(list)(
                SecretCoffeeMeeting.objects.select_related('employee1', 'employee2').all()[:2]
            )
            for meeting in meetings:
                print(f"   - Встреча {meeting.meeting_id}: {meeting.employee1.full_name} & {meeting.employee2.full_name}")
                print(f"     Коды: {meeting.employee1_code} / {meeting.employee2_code}")
                print(f"     Знак: {meeting.recognition_sign}")
    except Exception as e:
        print(f"   Ошибка проверки встреч: {e}")
    
    print("✅ Тестирование анонимного кофе завершено!")

if __name__ == "__main__":
    asyncio.run(test_anonymous_coffee())