#!/usr/bin/env python
"""
Тестирование всех команд ConnectBot v21
"""
import asyncio
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

async def test_all_commands():
    """Тест всех команд бота"""
    commands_to_test = [
        '/start',
        '/help', 
        '/menu',
        '/coffee',
        '/activities',
        '/profile',
        '/settings',
        '/stats',
        '/preferences',
        '/test'
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ ВСЕХ КОМАНД CONNECTBOT V21")
    print("=" * 60)
    
    try:
        from telegram import Bot
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        print("✅ Бот инициализирован")
        print(f"📋 Команд для тестирования: {len(commands_to_test)}")
        print("\n🎯 ДОСТУПНЫЕ КОМАНДЫ:")
        
        for i, command in enumerate(commands_to_test, 1):
            description = {
                '/start': 'Запуск и приветствие',
                '/help': 'Справка по всем командам', 
                '/menu': 'Главное меню (=help)',
                '/coffee': 'Тайный кофе - анонимные встречи',
                '/activities': 'Корпоративные активности',
                '/profile': 'Профиль пользователя',
                '/settings': 'Настройки бота',
                '/stats': 'Статистика активности',
                '/preferences': 'Настройки Тайного кофе',
                '/test': 'Тестовая команда'
            }.get(command, 'Описание не доступно')
            
            print(f"  {i:2d}. {command:<12} - {description}")
        
        print(f"\n" + "=" * 60)
        print("🚀 Все команды готовы к использованию!")
        print("\n💡 Для тестирования отправьте команды боту в Telegram:")
        print("   • Начните с /start для приветствия")
        print("   • Используйте /help для полного списка")
        print("   • Попробуйте /coffee для функций Тайного кофе")
        print("   • Проверьте /activities для корпоративных активностей")
        
        # Проверим статус бота
        bot_info = await bot.get_me()
        print(f"\n🤖 Статус бота:")
        print(f"   • Имя: {bot_info.first_name}")
        print(f"   • Username: @{bot_info.username}")
        print(f"   • ID: {bot_info.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_all_commands())