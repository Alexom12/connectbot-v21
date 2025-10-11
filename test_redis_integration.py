#!/usr/bin/env python
"""
Тестирование Redis интеграции ConnectBot
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.redis_utils import RedisManager
from employees.redis_integration import redis_integration
import json

def test_redis_integration():
    print('=== REDIS INTEGRATION TEST ===')
    print(f'Redis available: {RedisManager.is_redis_available()}')
    print()
    
    print('=== REDIS HEALTH ===')
    try:
        health = redis_integration.health_check()
        print(f'Health status: {health}')
    except Exception as e:
        print(f'Health check failed: {e}')
    print()
    
    print('=== TESTING EMPLOYEE CACHE ===')
    # Тест кэширования сотрудника
    test_employee_data = {
        'id': 123,
        'name': 'Test Employee',
        'position': 'Test Position',
        'department': 'Test Department'
    }
    
    success = RedisManager.cache_employee_data(123, test_employee_data, 60)
    print(f'Employee data cached: {success}')
    
    cached_employee = RedisManager.get_employee_data(123)
    print(f'Cached employee: {cached_employee}')
    print(f'Data matches: {cached_employee == test_employee_data if cached_employee else False}')
    print()
    
    print('=== TESTING BOT SESSION ===')
    # Тест сессии бота
    test_session = {
        'user_id': 456,
        'current_menu': 'main',
        'last_action': 'profile_view'
    }
    
    session_stored = RedisManager.store_bot_session(456, test_session, 300)
    print(f'Bot session stored: {session_stored}')
    
    retrieved_session = RedisManager.get_bot_session(456)
    print(f'Retrieved session: {retrieved_session}')
    
    print()
    print('=== TESTING USER EVENT PUBLISHING ===')
    try:
        event_success = redis_integration.events.publish_user_event(789, 'test_event', {'message': 'Hello Redis!'})
        print(f'Event published: {event_success}')
    except Exception as e:
        print(f'Event publishing failed: {e}')
    
    print()
    print('=== TESTING ACTIVITY MANAGER ===')
    from activities.services import ActivityManager
    from employees.models import Employee
    
    # Получаем первых двух сотрудников для тестирования
    employees = list(Employee.objects.all()[:2])
    if len(employees) >= 2:
        print(f'Testing with employees: {employees[0].full_name}, {employees[1].full_name}')
        
        # Создаем менеджер активностей
        manager = ActivityManager()
        print('ActivityManager created successfully')
        
        # Тестируем синхронную версию создания сессий (пока что)
        try:
            # Создаем тестовую сессию для демонстрации
            from activities.models import ActivitySession
            from django.utils import timezone
            from datetime import timedelta
            
            today = timezone.now().date()
            next_monday = today + timedelta(days=(7 - today.weekday()))
            
            session, created = ActivitySession.objects.get_or_create(
                activity_type='chess',
                week_start=next_monday,
                defaults={'status': 'planned'}
            )
            print(f'Test session: {session} (created: {created})')
            
        except Exception as e:
            print(f'ActivityManager test failed: {e}')
    else:
        print('Not enough employees for testing')

if __name__ == "__main__":
    test_redis_integration()