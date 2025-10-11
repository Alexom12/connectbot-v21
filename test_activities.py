import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from activities.services import ActivityManager
from activities.models import ActivitySession
from datetime import datetime, timedelta

async def test_activities():
    print("🧪 Тестирование системы активностей...")
    
    manager = ActivityManager()
    
    # Тест создания сессий
    print("1. Создание недельных сессий...")
    success = await manager.create_weekly_sessions()
    print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
    
    # Проверяем созданные сессии
    from asgiref.sync import sync_to_async
    
    sessions = await sync_to_async(list)(ActivitySession.objects.all())
    print(f"2. Создано сессий: {len(sessions)}")
    
    for session in sessions:
        display_name = await sync_to_async(session.get_activity_type_display)()
        print(f"   - {session.activity_type} ({display_name}): {session.week_start} ({session.status})")
    
    # Тест получения участников
    print("3. Тест получения участников...")
    participants = await manager.get_participants('secret_coffee')
    print(f"   Участников тайного кофе: {len(participants)}")
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_activities())