"""
Минималистичный бот с максимальной отказоустойчивостью
"""
import os
import sys
import time
import requests
from pathlib import Path
import urllib3

# Отключаем предупреждения SSL для тестирования
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from employees.models import Employee

class MinimalBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.offset = 0
        
        # Создаем сессию с агрессивными настройками
        self.session = requests.Session()
        
        # Отключаем SSL проверку для тестирования
        self.session.verify = False
        
        # Устанавливаем минимальные таймауты
        self.session.timeout = (3, 5)  # (connect, read)
        
        # Отключаем keep-alive для избежания проблем с соединениями
        self.session.headers.update({
            'Connection': 'close',
            'User-Agent': 'MinimalBot/1.0'
        })
    
    def safe_request(self, method, endpoint, **kwargs):
        """Безопасный HTTP запрос"""
        url = self.base_url + endpoint
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            else:
                response = self.session.post(url, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"Сетевая ошибка: {type(e).__name__}")
        
        return None
    
    def get_bot_info(self):
        """Проверить подключение к боту"""
        result = self.safe_request('GET', 'getMe')
        if result and result.get('ok'):
            return result['result']
        return None
    
    def get_updates(self):
        """Получить обновления с минимальным таймаутом"""
        params = {
            'offset': self.offset,
            'timeout': 1,
            'limit': 1
        }
        
        result = self.safe_request('GET', 'getUpdates', params=params)
        if result and result.get('ok'):
            return result['result']
        return []
    
    def send_message(self, chat_id, text):
        """Отправить сообщение"""
        data = {
            'chat_id': chat_id,
            'text': text[:4000]  # Ограничиваем длину
        }
        
        result = self.safe_request('POST', 'sendMessage', data=data)
        if result and result.get('ok'):
            print(f"✅ Отправлено в {chat_id}")
            return True
        
        print(f"❌ Не отправлено в {chat_id}")
        return False
    
    def handle_message(self, message):
        """Обработка сообщения"""
        chat_id = message['chat']['id']
        user = message.get('from', {})
        text = message.get('text', '')
        
        user_id = user.get('id')
        username = user.get('username', user.get('first_name', 'Unknown'))
        
        print(f"📩 {username}({user_id}): {text}")
        
        # Простая обработка команд
        if text == '/start':
            response = self.cmd_start(user_id, username)
        elif text == '/info':
            response = f"ℹ️ Бот: @ConnectBot_BG_TEST_bot\\nВремя: {time.strftime('%H:%M:%S')}"
        elif text == '/ping':
            response = "🏓 pong!"
        else:
            response = f"Получено: {text}\\n\\nКоманды:\\n/start - авторизация\\n/info - информация\\n/ping - тест"
        
        return self.send_message(chat_id, response)
    
    def cmd_start(self, user_id, username):
        """Команда /start"""
        try:
            employee = Employee.objects.filter(telegram_id=user_id, is_active=True).first()
            
            if not employee:
                employee = Employee.objects.filter(
                    telegram_username__iexact=username, 
                    is_active=True
                ).first()
                if employee:
                    employee.telegram_id = user_id
                    employee.save()
            
            if employee:
                return (
                    f"✅ {employee.full_name}\\n"
                    f"🏢 {employee.position}\\n"
                    f"🤖 Бот работает!"
                )
            else:
                return f"❌ {username} не авторизован"
                
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def run_minimal(self):
        """Минималистичный запуск"""
        print("🤖 Запуск минимального бота...")
        
        # Проверяем подключение
        retries = 0
        while retries < 10:
            bot_info = self.get_bot_info()
            if bot_info:
                print(f"✅ @{bot_info['username']}")
                break
            retries += 1
            print(f"Попытка {retries}/10...")
            time.sleep(1)
        
        if not bot_info:
            print("❌ Не удалось подключиться")
            return
        
        print("🔄 Polling...")
        
        failures = 0
        max_failures = 50
        
        while failures < max_failures:
            try:
                updates = self.get_updates()
                
                if updates:
                    failures = 0
                    for update in updates:
                        self.offset = update['update_id'] + 1
                        if 'message' in update:
                            self.handle_message(update['message'])
                else:
                    time.sleep(0.2)
                    
            except KeyboardInterrupt:
                print("\\n👋 Остановка")
                break
            except Exception as e:
                failures += 1
                print(f"Ошибка {failures}/{max_failures}: {type(e).__name__}")
                time.sleep(0.5)
        
        if failures >= max_failures:
            print(f"💥 Превышен лимит ошибок")

if __name__ == '__main__':
    bot = MinimalBot()
    bot.run_minimal()