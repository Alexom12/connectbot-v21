#!/usr/bin/env python
"""
Тестовый скрипт для проверки команд бота
Проверяет доступность Telegram API и имитирует отправку команд
"""
import asyncio
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

async def test_bot_api():
    """Тест доступности API Telegram"""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        
        print("🤖 Проверка доступности Telegram API...")
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот найден: @{bot_info.username}")
        print(f"📝 Имя: {bot_info.first_name}")
        print(f"🆔 ID: {bot_info.id}")
        
        # Проверяем вебхуки (должны быть выключены для polling)
        webhook_info = await bot.get_webhook_info()
        print(f"🔗 Webhook URL: {webhook_info.url or 'Не установлен (правильно для polling)'}")
        
        return True
        
    except TelegramError as e:
        print(f"❌ Ошибка Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

async def check_bot_updates():
    """Проверка последних обновлений"""
    try:
        from telegram import Bot
        
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        print("\n📥 Проверка последних обновлений...")
        
        # Получаем последние обновления без их обработки
        updates = await bot.get_updates(limit=10, timeout=5)
        
        if updates:
            print(f"📨 Найдено {len(updates)} обновлений:")
            for update in updates[-3:]:  # Показываем только последние 3
                if update.message:
                    user = update.message.from_user
                    text = update.message.text or "[Не текстовое сообщение]"
                    print(f"  👤 @{user.username or user.first_name}: {text}")
        else:
            print("📭 Новых обновлений нет")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при получении обновлений: {e}")
        return False

def test_handlers_registration():
    """Проверка регистрации обработчиков команд"""
    try:
        print("\n🔧 Проверка регистрации обработчиков...")
        
        # Импортируем команду бота
        from bots.management.commands.runbot import Command
        
        # Проверяем есть ли метод регистрации обработчиков
        cmd = Command()
        if hasattr(cmd, '_setup_basic_handlers'):
            print("✅ Метод _setup_basic_handlers найден")
            
            # Проверим, что в коде есть нужные команды
            import inspect
            source = inspect.getsource(cmd._setup_basic_handlers)
            
            commands = ['start', 'help', 'test']
            for command in commands:
                if f'"{command}"' in source:
                    print(f"✅ Команда /{command} зарегистрирована")
                else:
                    print(f"⚠️ Команда /{command} НЕ найдена в коде")
                    
            return True
        else:
            print("❌ Метод _setup_basic_handlers НЕ найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке обработчиков: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🧪 ConnectBot v21 - Диагностика команд")
    print("=" * 50)
    
    # Тест 1: API доступность
    api_ok = await test_bot_api()
    
    # Тест 2: Проверка обработчиков
    handlers_ok = test_handlers_registration()
    
    # Тест 3: Проверка обновлений
    updates_ok = await check_bot_updates()
    
    print("\n" + "=" * 50)
    print("📊 Результаты диагностики:")
    print(f"🌐 API доступность: {'✅ OK' if api_ok else '❌ FAIL'}")
    print(f"🔧 Обработчики команд: {'✅ OK' if handlers_ok else '❌ FAIL'}")
    print(f"📥 Получение обновлений: {'✅ OK' if updates_ok else '❌ FAIL'}")
    
    if all([api_ok, handlers_ok, updates_ok]):
        print("\n🎉 Все тесты пройдены! Бот должен реагировать на команды.")
        print("\n💡 Попробуйте отправить боту команды:")
        print("   /start - Приветствие")
        print("   /help - Справка")
        print("   /test - Тестовая команда")
    else:
        print("\n⚠️ Обнаружены проблемы. Проверьте настройки бота.")

if __name__ == "__main__":
    asyncio.run(main())