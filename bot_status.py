#!/usr/bin/env python3
"""
🤖 Информация о запущенном ConnectBot
"""

import os
import sys
import django
from datetime import datetime

# Настройка Django
def setup_django():
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

setup_django()

from django.conf import settings
from employees.models import Employee

def main():
    """Показывает информацию о ConnectBot"""
    
    print("🤖" + "="*60 + "🤖")
    print("📊 ИНФОРМАЦИЯ О CONNECTBOT V21")
    print("🤖" + "="*60 + "🤖")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Информация о боте
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if bot_token:
        print("🚀 Статус бота:")
        print(f"   ✅ Токен настроен: {bot_token[:20]}...")
        print(f"   📟 Длина токена: {len(bot_token)} символов")
    else:
        print("❌ Токен бота не настроен!")
    
    print()
    
    # Информация о базе данных
    print("💾 Статус базы данных:")
    try:
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        authorized_employees = Employee.objects.filter(authorized=True).count()
        
        print(f"   👥 Всего сотрудников: {total_employees}")
        print(f"   ✅ Активных: {active_employees}")
        print(f"   🔑 Авторизованных: {authorized_employees}")
        
        if authorized_employees > 0:
            print("   📋 Авторизованные пользователи:")
            for emp in Employee.objects.filter(authorized=True)[:5]:
                username = emp.telegram_username or "Нет username"
                print(f"      • {emp.full_name} (@{username})")
            
            if authorized_employees > 5:
                print(f"      ... и еще {authorized_employees - 5}")
        
    except Exception as e:
        print(f"   ❌ Ошибка доступа к БД: {e}")
    
    print()
    
    # Информация о Redis
    print("🗄️ Статус Redis:")
    try:
        from employees.redis_integration import redis_integration
        health = redis_integration.health_check()
        
        if health.get('redis_available'):
            print(f"   ✅ Redis доступен: {health.get('status')}")
            print(f"   🔗 URL: {health.get('redis_url')}")
        else:
            print(f"   ❌ Redis недоступен: {health.get('error', 'Неизвестная ошибка')}")
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки Redis: {e}")
    
    print()
    
    # Информация о Java сервисе
    print("☕ Статус Java микросервиса:")
    try:
        import requests
        java_url = getattr(settings, 'JAVA_SERVICE_URL', 'http://localhost:8080')
        
        response = requests.get(f"{java_url}/api/matching/health", timeout=5)
        if response.status_code in [200, 503]:
            health_data = response.json()
            status = health_data.get('overall_status', health_data.get('status'))
            print(f"   ✅ Java сервис доступен: {status}")
            print(f"   🔗 URL: {java_url}")
            print(f"   📊 Версия: {health_data.get('version')}")
        else:
            print(f"   ❌ Java сервис недоступен: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Java сервис недоступен: {e}")
    
    print()
    
    # Команды для работы с ботом
    print("🛠️ Команды управления:")
    print("   Запуск бота: python manage.py runbot")
    print("   Остановка: Ctrl+C в терминале с ботом")
    print("   Тест бота: python test_bot.py")
    print("   Применить миграции: python manage.py migrate")
    print("   Создать суперпользователя: python manage.py createsuperuser")
    
    print()
    print("📱 Как протестировать бота:")
    print("   1. Найдите @ConnectBotTestBot в Telegram")
    print("   2. Отправьте команду /start")
    print("   3. Убедитесь, что ваш username есть в базе сотрудников")
    
    print()
    print("🤖" + "="*60 + "🤖")

if __name__ == "__main__":
    main()