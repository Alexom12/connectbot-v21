#!/usr/bin/env python
"""
Простой тест Telegram бота
"""
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text('🤖 ConnectBot работает!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text('Доступные команды:\n/start - начало работы\n/help - справка')

def main():
    """Запуск бота"""
    token = settings.TELEGRAM_BOT_TOKEN
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
    
    print(f"🤖 Запуск тестового бота...")
    print(f"📟 Токен: {token[:20]}...")
    
    # Создание приложения
    app = Application.builder().token(token).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Бот запущен и ожидает сообщений...")
    print("Для остановки нажмите Ctrl+C")
    
    # Запуск polling
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")