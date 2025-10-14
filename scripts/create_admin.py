# scripts/create_admin.py

import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee, AdminUser


async def create_superuser_via_django():
    """Создает суперпользователя через Django createsuperuser"""
    print("""
🎯 ДЛЯ СОЗДАНИЯ АДМИНИСТРАТОРОВ ИСПОЛЬЗУЙТЕ DJANGO ADMIN:

1. Создайте суперпользователя (если еще нет):
   python manage.py createsuperuser

2. Зайдите в Django Admin:
   http://localhost:8000/admin/

3. Управляйте администраторами в разделе "Employees"

📋 Преимущества Django Admin:
• Визуальный интерфейс
• Фильтрация и поиск
• История изменений
• Гибкие права доступа
• Логирование действий
    """)


async def list_admin_users():
    """Показывает список всех администраторов"""
    print("👥 СПИСОК АДМИНИСТРАТОРОВ:")
    print("-" * 50)
    
    async for admin in AdminUser.objects.select_related('user').all():
        status = "✅ Активен" if admin.is_active else "❌ Неактивен"
        print(f"• {admin.user.full_name} (@{admin.user.telegram_username})")
        print(f"  Роль: {admin.role} | {status}")
        print(f"  Создан: {admin.created_at.strftime('%d.%m.%Y')}")
        print()


async def main():
    """Основная функция"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        await list_admin_users()
    else:
        await create_superuser_via_django()

if __name__ == "__main__":
    asyncio.run(main())