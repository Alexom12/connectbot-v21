"""
Простейший Telegram бот на requests для обхода проблем с python-telegram-bot
"""
import os
import sys
import time
import requests
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from employees.utils import AuthManager

class SimpleTelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.offset = 0
        self.session = requests.Session()
        # Увеличиваем таймауты для requests
        self.session.timeout = 30
        
    def get_me(self):
        """Получить информацию о боте"""
        try:
            response = self.session.get(self.base_url + "getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return data['result']
            return None
        except Exception as e:
            print(f"Ошибка get_me: {e}")
            return None
    
    def get_updates(self):
        """Получить обновления с обработкой таймаутов"""
        try:
            params = {
                'offset': self.offset,
                'timeout': 5,  # Очень короткий таймаут
                'limit': 10
            }
            
            response = self.session.get(
                self.base_url + "getUpdates", 
                params=params, 
                timeout=10  # Короткий общий таймаут
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return data['result']
            return []
            
        except Exception as e:
            # Не печатаем ошибки таймаута, они нормальны
            if "timed out" not in str(e).lower():
                print(f"Ошибка get_updates: {e}")
            return []
    
    def send_message(self, chat_id, text):
        """Отправить сообщение с повторными попытками"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                params = {
                    'chat_id': chat_id,
                    'text': text
                }
                
                response = self.session.post(
                    self.base_url + "sendMessage", 
                    data=params, 
                    timeout=30  # Увеличили таймаут
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['ok']:
                        print(f"✅ Сообщение отправлено в чат {chat_id}")
                        return True
                
                print(f"❌ Ошибка API: {response.status_code} - {response.text[:100]}")
                return False
                
            except Exception as e:
                print(f"❌ Ошибка отправки (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                    
        return False
    
    def process_message(self, message):
        """Обработать сообщение"""
        chat_id = message['chat']['id']
        user = message.get('from', {})
        text = message.get('text', '')
        
        user_id = user.get('id')
        username = user.get('username') or user.get('first_name') or str(user_id)
        
        print(f"Сообщение от {username} (ID: {user_id}): {text}")
        
        # Обработка команд
        if text == '/start':
            return self.handle_start(chat_id, user_id, username)
        elif text == '/status':
            return self.handle_status(chat_id)
        elif text == '/help':
            return self.handle_help(chat_id)
        else:
            return self.handle_text(chat_id, text)
    
    def handle_start(self, chat_id, user_id, username):
        """Обработка команды /start"""
        try:
            # Создаем объект пользователя в формате, ожидаемом AuthManager
            class TelegramUser:
                def __init__(self, user_id, username, first_name):
                    self.id = user_id
                    self.username = username  
                    self.first_name = first_name
            
            telegram_user = TelegramUser(user_id, username, username)
            
            # Используем метод authorize_employee из AuthManager
            from asgiref.sync import sync_to_async
            import asyncio
            
            # Запускаем асинхронную авторизацию синхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                employee, is_new = loop.run_until_complete(
                    AuthManager.authorize_employee(telegram_user)
                )
            finally:
                loop.close()
            
            if employee:
                text = (
                    f"✅ Привет, {employee.full_name}!\\n"
                    f"🏢 Позиция: {employee.position}\\n"
                    f"🏬 Департамент: {employee.department}\\n"
                    f"📧 Email: {employee.email}\\n\\n"
                    f"🤖 ConnectBot работает на requests!\\n"
                    f"Команды: /status /help"
                )
                if is_new:
                    text += "\\n\\n🎉 Добро пожаловать! Вы успешно зарегистрированы."
            else:
                text = f"❌ Доступ запрещен для {username}\\nОбратитесь к администратору."
                    
            return self.send_message(chat_id, text)
            
        except Exception as e:
            print(f"Ошибка handle_start: {e}")
            return self.send_message(chat_id, "❌ Техническая ошибка")
    
    def handle_status(self, chat_id):
        """Обработка команды /status"""
        try:
            from employees.models import Employee
            
            user_count = Employee.objects.filter(is_active=True).count()
            
            text = (
                f"📊 Статус ConnectBot\\n\\n"
                f"👥 Активных пользователей: {user_count}\\n"
                f"⏰ Время: {time.strftime('%H:%M:%S')}\\n"
                f"✅ Бот работает на requests"
            )
            
            return self.send_message(chat_id, text)
            
        except Exception as e:
            print(f"Ошибка handle_status: {e}")
            return self.send_message(chat_id, "❌ Ошибка получения статуса")
    
    def handle_help(self, chat_id):
        """Обработка команды /help"""
        text = (
            f"🆘 Помощь ConnectBot\\n\\n"
            f"/start - авторизация\\n"
            f"/status - статус бота\\n"
            f"/help - эта справка\\n\\n"
            f"Напишите любое сообщение для теста."
        )
        return self.send_message(chat_id, text)
    
    def handle_text(self, chat_id, text):
        """Обработка обычного текста"""
        response = f"📝 Получено: {text}\\n\\nКоманды: /start /status /help"
        return self.send_message(chat_id, response)
    
    def run(self):
        """Основной цикл бота"""
        print("🚀 Запуск простого ConnectBot на requests...")
        
        # Проверяем подключение к боту
        me = self.get_me()
        if not me:
            print("❌ Не удалось подключиться к боту")
            return
        
        print(f"✅ Бот подключен: @{me['username']} ({me['first_name']})")
        print("🔄 Начинаем получение обновлений...")
        
        error_count = 0
        max_errors = 10
        
        while True:
            try:
                updates = self.get_updates()
                
                if updates:
                    error_count = 0  # Сбрасываем счетчик ошибок при успехе
                    
                    for update in updates:
                        update_id = update['update_id']
                        self.offset = update_id + 1
                        
                        if 'message' in update:
                            self.process_message(update['message'])
                else:
                    # Если нет обновлений, ждем немного
                    time.sleep(1)
                
            except KeyboardInterrupt:
                print("\\n🛑 Остановка бота...")
                break
            except Exception as e:
                error_count += 1
                print(f"❌ Ошибка #{error_count}: {e}")
                
                if error_count >= max_errors:
                    print(f"💥 Слишком много ошибок ({max_errors}), останавливаемся...")
                    break
                
                # Пауза при ошибке
                time.sleep(min(5, error_count))
        
        print("👋 Бот остановлен")

if __name__ == '__main__':
    bot = SimpleTelegramBot()
    bot.run()