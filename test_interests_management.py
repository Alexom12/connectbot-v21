#!/usr/bin/env python3
"""
Тест функциональности управления интересами в ConnectBot
"""

import os
import sys
import django
import asyncio
import logging

# Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee, Interest, EmployeeInterest
from employees.utils import PreferenceManager
from bots.menu_manager import MenuManager

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_interests.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_interests_functionality():
    """Тестируем функциональность управления интересами"""
    
    print("🔍 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ИНТЕРЕСАМИ\n" + "="*50)
    
    # 1. Проверяем существующие интересы
    print("\n1. 📊 Проверяем доступные интересы...")
    try:
        all_interests = await PreferenceManager.get_all_interests()
        print(f"   ✅ Найдено интересов: {len(all_interests)}")
        
        if not all_interests:
            print("   ⚠️  Нет интересов в базе данных. Создаём базовые...")
            await create_default_interests()
            all_interests = await PreferenceManager.get_all_interests()
            print(f"   ✅ Создано интересов: {len(all_interests)}")
        
        for interest in all_interests:
            print(f"      • {interest.emoji} {interest.name} (код: {interest.code})")
            
    except Exception as e:
        print(f"   ❌ Ошибка получения интересов: {e}")
        return False
    
    # 2. Находим тестового сотрудника
    print("\n2. 👤 Ищем тестового сотрудника...")
    try:
        employee = await Employee.objects.afirst()
        if not employee:
            print("   ❌ Нет сотрудников в базе данных!")
            return False
        
        print(f"   ✅ Найден сотрудник: {employee.full_name}")
        print(f"      Telegram ID: {employee.telegram_id}")
        print(f"      Должность: {employee.position}")
        
    except Exception as e:
        print(f"   ❌ Ошибка поиска сотрудника: {e}")
        return False
    
    # 3. Проверяем текущие интересы сотрудника
    print("\n3. 🎯 Проверяем текущие интересы сотрудника...")
    try:
        employee_interests = await PreferenceManager.get_employee_interests(employee)
        active_interests = [ei for ei in employee_interests if ei.is_active]
        
        print(f"   ✅ Всего записей интересов: {len(employee_interests)}")
        print(f"   ✅ Активных интересов: {len(active_interests)}")
        
        if active_interests:
            for ei in active_interests:
                print(f"      • ✅ {ei.interest.emoji} {ei.interest.name}")
        else:
            print("      📝 Нет активных интересов")
            
    except Exception as e:
        print(f"   ❌ Ошибка получения интересов сотрудника: {e}")
        return False
    
    # 4. Тестируем создание меню интересов
    print("\n4. 📱 Тестируем создание меню управления интересами...")
    try:
        menu_data = await MenuManager.create_interests_menu(employee)
        
        print("   ✅ Меню успешно создано!")
        print(f"   📝 Текст меню:")
        print("   " + "\n   ".join(menu_data['text'].split('\n')))
        
        # Проверяем кнопки
        keyboard = menu_data['reply_markup'].inline_keyboard
        print(f"\n   🔘 Кнопок в меню: {len(keyboard)}")
        
        interest_buttons = []
        for row in keyboard:
            for button in row:
                if 'toggle_interest_' in button.callback_data:
                    interest_buttons.append(button)
        
        print(f"   🎯 Кнопок интересов: {len(interest_buttons)}")
        
        for button in interest_buttons[:5]:  # Показываем первые 5
            status = "✅" if "✅" in button.text else "❌"
            print(f"      {status} {button.text.replace('✅ ', '').replace('❌ ', '')}")
            
    except Exception as e:
        print(f"   ❌ Ошибка создания меню: {e}")
        return False
    
    # 5. Тестируем обновление интересов
    print("\n5. 🔄 Тестируем обновление интересов...")
    try:
        # Выбираем первые 2 интереса для активации
        test_interests = all_interests[:2] if len(all_interests) >= 2 else all_interests
        test_codes = [interest.code for interest in test_interests]
        
        print(f"   📝 Активируем интересы: {test_codes}")
        
        result = await PreferenceManager.update_employee_interests(employee, test_codes)
        
        if result:
            print("   ✅ Интересы успешно обновлены!")
            
            # Проверяем результат
            updated_interests = await PreferenceManager.get_employee_interests(employee)
            active_after = [ei for ei in updated_interests if ei.is_active]
            
            print(f"   ✅ Активных интересов после обновления: {len(active_after)}")
            for ei in active_after:
                print(f"      • ✅ {ei.interest.emoji} {ei.interest.name}")
                
        else:
            print("   ❌ Не удалось обновить интересы")
            
    except Exception as e:
        print(f"   ❌ Ошибка обновления интересов: {e}")
        return False
    
    # 6. Тестируем отключение всех интересов
    print("\n6. ❌ Тестируем отключение всех интересов...")
    try:
        result = await PreferenceManager.disable_all_interests(employee)
        
        if result:
            print("   ✅ Все интересы отключены!")
            
            # Проверяем результат
            final_interests = await PreferenceManager.get_employee_interests(employee)
            active_final = [ei for ei in final_interests if ei.is_active]
            
            print(f"   ✅ Активных интересов после отключения: {len(active_final)}")
            
        else:
            print("   ❌ Не удалось отключить все интересы")
            
    except Exception as e:
        print(f"   ❌ Ошибка отключения интересов: {e}")
        return False
    
    print("\n" + "="*50)
    print("✅ ВСЕ ТЕСТЫ УПРАВЛЕНИЯ ИНТЕРЕСАМИ ПРОЙДЕНЫ!")
    return True

async def create_default_interests():
    """Создаём базовые интересы для тестирования"""
    from asgiref.sync import sync_to_async
    
    interests_data = [
        ('secret_coffee', 'Тайный кофе', '☕️', 'Встречи за чашкой кофе с коллегами'),
        ('chess', 'Шахматы', '♟️', 'Интеллектуальные шахматные поединки'),
        ('ping_pong', 'Настольный теннис', '🏓', 'Активные игры в пинг-понг'),
        ('photo_quest', 'Фотоквесты', '📸', 'Творческие фотозадания и конкурсы'),
        ('workshop', 'Мастер-классы', '🧠', 'Образовательные мероприятия и воркшопы'),
        ('lunch_blind', 'Обед вслепую', '🍽️', 'Совместные обеды с новыми людьми'),
        ('board_games', 'Настольные игры', '🎲', 'Вечера настольных игр'),
        ('sport_events', 'Спортивные события', '⚽️', 'Корпоративные спортивные мероприятия'),
        ('book_club', 'Книжный клуб', '📚', 'Обсуждение книг с коллегами'),
        ('tech_talks', 'Tech talks', '💻', 'Технические презентации и доклады')
    ]
    
    @sync_to_async
    def create_interests():
        created_count = 0
        for code, name, emoji, description in interests_data:
            interest, created = Interest.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'emoji': emoji,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                created_count += 1
        return created_count
    
    count = await create_interests()
    print(f"   ✅ Создано новых интересов: {count}")

async def main():
    """Главная функция тестирования"""
    try:
        print("🚀 Запуск тестирования управления интересами ConnectBot...")
        
        success = await test_interests_functionality()
        
        if success:
            print("\n🎉 Все тесты прошли успешно!")
            print("\n💡 Для полного тестирования:")
            print("   1. Запустите бот: python manage.py runbot")
            print("   2. Найдите бота в Telegram")
            print("   3. Отправьте /start")
            print("   4. Нажмите 'Мои интересы' в главном меню")
            print("   5. Протестируйте переключение интересов")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        sys.exit(1)