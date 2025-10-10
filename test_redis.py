#!/usr/bin/env python
"""
Тестирование Redis интеграции ConnectBot v21
"""
import os
import sys
import django

# Настройка Django
sys.path.append(r'E:\ConnectBot v21')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.redis_utils import RedisManager
from django.core.cache import cache

def test_redis_integration():
    """Тестирование Redis интеграции"""
    print("🧪 Тестирование Redis интеграции ConnectBot v21")
    print("=" * 50)
    
    # Тест 1: Проверка доступности Redis
    print("\n1️⃣  Проверка доступности Redis:")
    if RedisManager.is_redis_available():
        print("   ✅ Redis доступен")
        redis_status = "✅ Доступен"
    else:
        print("   ⚠️  Redis недоступен (будет использоваться Django кеш)")
        redis_status = "⚠️  Недоступен"
    
    # Тест 2: Базовые функции кеширования Django
    print("\n2️⃣  Тест базового кеширования Django:")
    try:
        cache.set('test_django_cache', {'test': 'value'}, 30)
        result = cache.get('test_django_cache')
        cache.delete('test_django_cache')
        
        if result and result.get('test') == 'value':
            print("   ✅ Django кеш работает")
            django_cache_status = "✅ Работает"
        else:
            print("   ❌ Проблемы с Django кешем")
            django_cache_status = "❌ Не работает"
            
    except Exception as e:
        print(f"   ❌ Ошибка Django кеша: {e}")
        django_cache_status = f"❌ Ошибка: {e}"
    
    # Тест 3: Функции RedisManager
    print("\n3️⃣  Тест функций RedisManager:")
    results = {}
    
    try:
        # Тест кеширования данных сотрудника
        print("   📝 Тестирование кеширования сотрудников...")
        test_employee_data = {
            'id': 999,
            'full_name': 'Тестовый Сотрудник',
            'position': 'QA Engineer',
            'telegram_id': 123456789,
            'telegram_username': 'test_user',
        }
        
        success = RedisManager.cache_employee_data(123456789, test_employee_data)
        results['employee_cache'] = "✅ Работает" if success else "❌ Не работает"
        print(f"      Кеширование: {'✅' if success else '❌'}")
        
        cached_data = RedisManager.get_employee_data(123456789)
        cache_retrieval_success = cached_data and cached_data.get('full_name') == 'Тестовый Сотрудник'
        results['employee_retrieval'] = "✅ Работает" if cache_retrieval_success else "❌ Не работает"
        print(f"      Получение: {'✅' if cache_retrieval_success else '❌'}")
        
        # Тест кеширования интересов
        print("   🎯 Тестирование кеширования интересов...")
        test_interests = [
            {'code': 'coffee', 'name': 'Тайный кофе'},
            {'code': 'lunch', 'name': 'Обед вслепую'}
        ]
        
        success = RedisManager.cache_employee_interests(999, test_interests)
        results['interests_cache'] = "✅ Работает" if success else "❌ Не работает"
        print(f"      Кеширование интересов: {'✅' if success else '❌'}")
        
        cached_interests = RedisManager.get_employee_interests(999)
        interests_retrieval_success = cached_interests and len(cached_interests) == 2
        results['interests_retrieval'] = "✅ Работает" if interests_retrieval_success else "❌ Не работает"
        print(f"      Получение интересов: {'✅' if interests_retrieval_success else '❌'}")
        
        # Тест сессий бота
        print("   🤖 Тестирование сессий бота...")
        test_session = {
            'current_menu': 'main',
            'user_state': 'active',
            'last_command': '/start',
            'pending_interests': {'coffee': True}
        }
        
        success = RedisManager.store_bot_session(123456789, test_session)
        results['session_store'] = "✅ Работает" if success else "❌ Не работает"
        print(f"      Сохранение сессии: {'✅' if success else '❌'}")
        
        retrieved_session = RedisManager.get_bot_session(123456789)
        session_retrieval_success = (retrieved_session and 
                                   retrieved_session.get('current_menu') == 'main' and
                                   retrieved_session.get('pending_interests', {}).get('coffee') == True)
        results['session_retrieval'] = "✅ Работает" if session_retrieval_success else "❌ Не работает"
        print(f"      Получение сессии: {'✅' if session_retrieval_success else '❌'}")
        
        # Тест очистки кеша
        print("   🧹 Тестирование очистки кеша...")
        clear_success = RedisManager.clear_bot_session(123456789)
        invalidate_success = RedisManager.invalidate_employee_cache(123456789)
        
        results['cache_clear'] = "✅ Работает" if clear_success and invalidate_success else "❌ Не работает"
        print(f"      Очистка кеша: {'✅' if clear_success and invalidate_success else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Общая ошибка тестирования: {e}")
        results['general_error'] = f"❌ {e}"
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 50)
    print(f"Redis статус:           {redis_status}")
    print(f"Django кеш:             {django_cache_status}")
    print()
    print("Функции RedisManager:")
    for test_name, status in results.items():
        test_display = {
            'employee_cache': 'Кеш сотрудников',
            'employee_retrieval': 'Получение данных сотрудника',
            'interests_cache': 'Кеш интересов',
            'interests_retrieval': 'Получение интересов',
            'session_store': 'Сохранение сессий',
            'session_retrieval': 'Получение сессий',
            'cache_clear': 'Очистка кеша'
        }
        print(f"  {test_display.get(test_name, test_name):25} {status}")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    if not RedisManager.is_redis_available():
        print("  • Для полной функциональности установите Docker и запустите Redis:")
        print("    docker-compose up -d")
        print("  • Пока Redis недоступен, будет использоваться Django кеш (locmem)")
    else:
        print("  • ✅ Redis настроен правильно!")
        print("  • Можно использовать все функции кеширования")
    
    print()
    print("🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_redis_integration()