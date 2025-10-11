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
    from runbot import ConnectBot
    import asyncio
    
    print("🚀 Запуск ConnectBot...")
    bot = ConnectBot()
    asyncio.run(bot.run())

def scheduler_status():
    """Показать статус планировщика"""
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

def start_scheduler():
    """Запуск только планировщика"""
    from bots.services.scheduler_service import scheduler_service
    
    print("📅 Запуск планировщика...")
    scheduler_service.start_scheduler()
    
    if scheduler_service.is_running:
        print("✅ Планировщик запущен")
        scheduler_status()
    else:
        print("❌ Не удалось запустить планировщик")

def stop_scheduler():
    """Остановка планировщика"""
    from bots.services.scheduler_service import scheduler_service
    
    print("🛑 Остановка планировщика...")
    scheduler_service.stop_scheduler()
    print("✅ Планировщик остановлен")

def test_services():
    """Тестирование сервисов"""
    import asyncio
    from activities.services.activity_manager import ActivityManager
    from activities.services.anonymous_coffee_service import anonymous_coffee_service
    
    async def test():
        print("🧪 Тестирование сервисов...")
        
        # Тест менеджера активностей
        print("1. Тест ActivityManager...")
        manager = ActivityManager()
        success = await manager.create_weekly_sessions()
        print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        
        # Тест Тайного кофе
        print("2. Тест AnonymousCoffeeService...")
        success = await anonymous_coffee_service.run_weekly_matching()
        print(f"   Результат: {'✅ Успех' if success else '❌ Ошибка'}")
        
        print("✅ Тестирование завершено!")
    
    asyncio.run(test())

def main():
    """Основная функция управления"""
    parser = argparse.ArgumentParser(description='Управление ConnectBot')
    parser.add_argument('command', choices=[
        'start', 'status', 'start-scheduler', 
        'stop-scheduler', 'test', 'simple'
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
        from runbot_simple import main as simple_main
        import asyncio
        asyncio.run(simple_main())

if __name__ == "__main__":
    main()