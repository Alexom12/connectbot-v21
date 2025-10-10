"""
Супер-стойкий бот с агрессивными retry попытками
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

class ReliableTelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.offset = 0
        
        # Конфигурация для надежности
        self.max_retries = 5
        self.base_timeout = 3
        self.max_timeout = 15
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ConnectBot/1.0',
            'Accept': 'application/json'
        })
    
    def robust_request(self, method, url, **kwargs):
        """Супер-надежный HTTP запрос с множественными попытками"""
        for attempt in range(self.max_retries):
            timeout = min(self.base_timeout * (2 ** attempt), self.max_timeout)
            
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=timeout, **kwargs)
                else:
                    response = self.session.post(url, timeout=timeout, **kwargs)
                
                if response.status_code == 200:
                    return response
                    
            except Exception as e:
                print(f"Попытка {attempt + 1}/{self.max_retries} неудачна: {type(e).__name__}")
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        
        return None
    
    def get_me(self):
        """Получить информацию о боте"""
        response = self.robust_request('GET', self.base_url + "getMe")
        if response:
            data = response.json()
            if data.get('ok'):
                return data['result']
        return None
    
    def get_updates(self):
        """Получить обновления"""
        params = {
            'offset': self.offset,
            'timeout': 1,  # Очень короткий таймаут для Telegram
            'limit': 5
        }
        
        response = self.robust_request('GET', self.base_url + "getUpdates", params=params)
        if response:
            data = response.json()
            if data.get('ok'):
                return data['result']
        return []
    
    def send_message(self, chat_id, text):
        """Отправить сообщение"""
        data = {
            'chat_id': chat_id,
            'text': text
        }
        
        response = self.robust_request('POST', self.base_url + "sendMessage", data=data)
        if response:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Сообщение отправлено в {chat_id}")
                return True
        
        print(f"❌ Не удалось отправить сообщение в {chat_id}")
        return False
    
    def process_message(self, message):
        """Обработать сообщение"""
        chat_id = message['chat']['id']
        user = message.get('from', {})
        text = message.get('text', '')
        
        user_id = user.get('id')
        username = user.get('username', user.get('first_name', str(user_id)))
        
        print(f"📨 {username} (ID:{user_id}): {text}")
        
        if text == '/start':
            response = self.handle_start(user_id, username)
        elif text == '/status':
            response = f"🤖 Бот работает!\\nВремя: {time.strftime('%H:%M:%S')}"
        elif text == '/help':
            response = "🆘 Команды:\\n/start - авторизация\\n/status - статус\\n/help - помощь"
        else:
            response = f"📝 Получено: {text}\\nКоманды: /start /status /help"
        
        return self.send_message(chat_id, response)
    
    def handle_start(self, user_id, username):
        """Быстрая обработка /start"""
        try:
            # Проверяем пользователя в базе напрямую
            from employees.models import Employee
            
            employee = Employee.objects.filter(
                telegram_id=user_id,
                is_active=True
            ).first()
            
            if employee:
                return (
                    f"✅ Привет, {employee.full_name}!\\n"
                    f"🏢 {employee.position}\\n"
                    f"🏬 {employee.department}\\n"
                    f"🤖 ConnectBot работает!"
                )
            else:
                # Пробуем найти по username
                employee = Employee.objects.filter(
                    telegram_username__iexact=username,
                    is_active=True
                ).first()
                
                if employee:
                    # Обновляем telegram_id
                    employee.telegram_id = user_id
                    employee.save()
                    return (
                        f"✅ Привет, {employee.full_name}!\\n"
                        f"🏢 {employee.position}\\n" 
                        f"🆔 Ваш ID обновлен: {user_id}\\n"
                        f"🤖 ConnectBot работает!"
                    )
                else:
                    return f"❌ Пользователь {username} не найден в базе.\\nОбратитесь к администратору."
                    
        except Exception as e:
            print(f"Ошибка handle_start: {e}")
            return "❌ Техническая ошибка авторизации"
    
    def run_persistent(self):
        """Запуск с максимальной устойчивостью"""
        print("🚀 Запуск супер-стойкого ConnectBot...")
        
        # Попробуем подключиться к боту
        connection_attempts = 0
        max_connection_attempts = 20
        
        while connection_attempts < max_connection_attempts:
            me = self.get_me()
            if me:
                print(f"✅ Подключен: @{me['username']} ({me['first_name']})")
                break
            
            connection_attempts += 1
            print(f"Попытка подключения {connection_attempts}/{max_connection_attempts}...")
            time.sleep(2)
        
        if not me:
            print("❌ Не удалось подключиться к боту после всех попыток")
            return
        
        print("🔄 Начинаем получение сообщений...")
        
        error_count = 0
        max_consecutive_errors = 20
        
        while True:
            try:
                updates = self.get_updates()
                
                if updates:
                    error_count = 0  # Сбрасываем счетчик при успехе
                    
                    for update in updates:
                        update_id = update['update_id']
                        self.offset = update_id + 1
                        
                        if 'message' in update:
                            try:
                                self.process_message(update['message'])
                            except Exception as e:
                                print(f"❌ Ошибка обработки сообщения: {e}")
                else:
                    # Пауза между запросами
                    time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\\n🛑 Остановка по Ctrl+C...")
                break
            except Exception as e:
                error_count += 1
                print(f"❌ Ошибка #{error_count}: {type(e).__name__}")
                
                if error_count >= max_consecutive_errors:
                    print(f"💥 Слишком много ошибок подряд ({max_consecutive_errors})")
                    break
                
                # Пауза при ошибках
                time.sleep(min(5, error_count * 0.5))
        
        print("👋 Бот остановлен")

if __name__ == '__main__':
    bot = ReliableTelegramBot()
    bot.run_persistent()