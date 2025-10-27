"""
Скрипт управления сервисами ConnectBot
"""
import os
import sys
import argparse

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

def start_bot():
    """Запуск бота"""
    try:
        from django.core.management import call_command
        
        print("🚀 Запуск ConnectBot с новой системой меню...")
        print("📱 Используется ReplyKeyboardMarkup для удобной навигации")
        print("💡 Основные функции доступны через кнопки внизу экрана")
        
        # Запускаем команду runbot через Django management
        call_command('runbot')
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        # Fallback: попробовать запустить через subprocess
        try:
            import subprocess
            subprocess.run([sys.executable, 'manage.py', 'runbot'], check=True)
        except Exception as fallback_error:
            print(f"❌ Fallback ошибка: {fallback_error}")

def scheduler_status():
    """Показать статус планировщика"""
    try:
        from bots.services.scheduler_service import scheduler_service
        
        status = scheduler_service.get_scheduler_status()
        
        print(f"📊 Статус планировщика: {status['status'].upper()}")
        print(f"📅 Задач: {status['job_count']}")
        
        if status['jobs']:
            print("\n🎯 Настроенные задачи:")
            for job in status['jobs']:
                print(f"   • {job['name']}")
                print(f"     ID: {job['id']}")
                print(f"     Следующий запуск: {job['next_run']}")
                print()
        else:
            print("\n📭 Нет активных задач планировщика")
            
    except Exception as e:
        print(f"❌ Ошибка получения статуса планировщика: {e}")

def start_scheduler():
    """Запуск только планировщика"""
    try:
        from bots.services.scheduler_service import scheduler_service
        
        print("📅 Запуск планировщика...")
        scheduler_service.start_scheduler()
        
        if scheduler_service.is_running:
            print("✅ Планировщик запущен")
            scheduler_status()
        else:
            print("❌ Не удалось запустить планировщика")
            
    except Exception as e:
        print(f"❌ Ошибка запуска планировщика: {e}")

def stop_scheduler():
    """Остановка планировщика"""
    try:
        from bots.services.scheduler_service import scheduler_service
        
        print("🛑 Остановка планировщика...")
        scheduler_service.stop_scheduler()
        print("✅ Планировщик остановлен")
        
    except Exception as e:
        print(f"❌ Ошибка остановки планировщика: {e}")

def test_services():
    """Тестирование сервисов"""
    import asyncio
    from activities.services.activity_manager import ActivityManager
    from activities.services.anonymous_coffee_service import anonymous_coffee_service
    
    async def test():
        print("🧪 Тестирование сервисов с новой системой меню...")
        
        # Тест менеджера активностей
        print("1. Тест ActivityManager...")
        try:
            manager = ActivityManager()
            success = await manager.create_weekly_sessions()
            print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        except Exception as e:
            print(f"   Результат: ❌ Ошибка - {e}")
        
        # Тест Тайного кофе
        print("2. Тест AnonymousCoffeeService...")
        try:
            success = await anonymous_coffee_service.run_weekly_matching()
            print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        except Exception as e:
            print(f"   Результат: ❌ Ошибка - {e}")
        
        # Тест системы меню
        print("3. Тест системы меню...")
        try:
            from bots.menu_manager import MenuManager
            menu_text = await MenuManager.create_main_menu_message()
            keyboard = await MenuManager.create_main_reply_keyboard()
            print(f"   Главное меню: ✅ Успех")
            print(f"   Клавиатура: ✅ Успех")
        except Exception as e:
            print(f"   Система меню: ❌ Ошибка - {e}")
        
        print("✅ Тестирование завершено!")
    
    asyncio.run(test())

def test_menu_system():
    """Тестирование системы меню"""
    print("🧪 Тестирование системы меню...")
    
    try:
        from bots.menu_manager import MenuManager
        import asyncio
        
        async def test_menus():
            # Тест главного меню
            main_menu = await MenuManager.create_main_menu_message()
            main_keyboard = await MenuManager.create_main_reply_keyboard()
            print("✅ Главное меню: создано успешно")
            
            # Тест профиля
            try:
                from employees.models import Employee
                # Создаем тестового сотрудника или используем существующего
                test_employee = await Employee.objects.afirst()
                if test_employee:
                    profile_text = await MenuManager.create_profile_menu(test_employee)
                    profile_keyboard = await MenuManager.create_profile_reply_keyboard()
                    print("✅ Меню профиля: создано успешно")
                else:
                    print("⚠️ Меню профиля: нет тестовых сотрудников")
            except Exception as e:
                print(f"⚠️ Меню профиля: ошибка - {e}")
            
            # Тест других меню
            interests_text = await MenuManager.create_interests_menu(test_employee) if test_employee else "Тестовый текст"
            interests_keyboard = await MenuManager.create_interests_reply_keyboard()
            print("✅ Меню интересов: создано успешно")
            
            calendar_text = await MenuManager.create_calendar_menu(test_employee) if test_employee else "Тестовый текст"
            calendar_keyboard = await MenuManager.create_calendar_reply_keyboard()
            print("✅ Меню календаря: создано успешно")
            
            settings_text = await MenuManager.create_settings_menu()
            settings_keyboard = await MenuManager.create_settings_reply_keyboard()
            print("✅ Меню настроек: создано успешно")
            
            help_text = await MenuManager.create_help_menu()
            help_keyboard = await MenuManager.create_help_reply_keyboard()
            print("✅ Меню помощи: создано успешно")
            
            coffee_text = await MenuManager.create_coffee_menu()
            coffee_keyboard = await MenuManager.create_coffee_reply_keyboard()
            print("✅ Меню кофе: создано успешно")
            
            print("\n🎉 Все меню созданы успешно!")
            print("📱 Система ReplyKeyboardMarkup готова к использованию")
            
        asyncio.run(test_menus())
        
    except Exception as e:
        print(f"❌ Ошибка тестирования системы меню: {e}")

def show_menu_preview():
    """Показать предварительный просмотр меню"""
    print("👀 Предварительный просмотр системы меню\n")
    
    print("📋 ГЛАВНОЕ МЕНЮ - Reply клавиатура:")
    print("┌─────────────────────────────────────┐")
    print("│ 👤 Мой профиль    🎯 Мои интересы   │")
    print("│ 📅 Календарь     🏅 Достижения     │")
    print("│ ☕ Тайный кофе    ⚙️ Настройки      │")
    print("│ ❓ Помощь                           │")
    print("└─────────────────────────────────────┘")
    
    print("\n👤 МЕНЮ ПРОФИЛЯ:")
    print("┌─────────────────────────────────────┐")
    print("│ 📊 Статистика   🏆 Мои достижения   │")
    print("│ 📈 Активность   ⬅️ Назад в меню     │")
    print("└─────────────────────────────────────┘")
    
    print("\n🎯 МЕНЮ ИНТЕРЕСОВ:")
    print("┌─────────────────────────────────────┐")
    print("│ 💾 Сохранить  🚫 Отписаться от всего│")
    print("│ ⬅️ Назад в меню                     │")
    print("└─────────────────────────────────────┘")
    
    print("\n☕ МЕНЮ ТАЙНОГО КОФЕ:")
    print("┌─────────────────────────────────────┐")
    print("│ 💬 Написать    📅 Предложить        │")
    print("│    сообщение        встречу         │")
    print("│ 📋 Инструкция  ⬅️ Назад в меню     │")
    print("└─────────────────────────────────────┘")
    
    print("\n💡 Преимущества новой системы:")
    print("• ✅ Постоянная навигация внизу экрана")
    print("• ✅ Быстрый доступ ко всем функциям")
    print("• ✅ Интуитивно понятный интерфейс")
    print("• ✅ Не требует запоминания команд")

def main():
    """Основная функция управления"""
    parser = argparse.ArgumentParser(description='Управление ConnectBot')
    parser.add_argument('command', choices=[
        'start', 'status', 'start-scheduler', 
        'stop-scheduler', 'test', 'simple', 'test-menu', 'menu-preview'
    ], help='Команда для выполнения')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        start_bot()
    elif args.command == 'status':
        scheduler_status()
    elif args.command == 'start-scheduler':
        start_scheduler()
    elif args.command == 'stop-scheduler':
        stop_scheduler()
    elif args.command == 'test':
        test_services()
    elif args.command == 'simple':
        # Run the Django management command 'runbot_simple'
        import subprocess
        try:
            subprocess.run([sys.executable, 'manage.py', 'runbot_simple'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска runbot_simple: {e}")
    elif args.command == 'test-menu':
        test_menu_system()
    elif args.command == 'menu-preview':
        show_menu_preview()

if __name__ == "__main__":
    main()