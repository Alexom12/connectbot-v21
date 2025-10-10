"""
Создаем временное решение - бот, который работает в режиме ожидания команд из файла
"""
import os
import sys
import time
import json
import requests
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from employees.models import Employee

class FileBasedBot:
    """Бот, который читает команды из файла и записывает ответы в файл"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.commands_file = "bot_commands.json"
        self.responses_file = "bot_responses.json"
        
    def process_start_command(self, user_id, username):
        """Обработка команды /start"""
        try:
            # Прямой поиск в базе
            employee = Employee.objects.filter(telegram_id=user_id, is_active=True).first()
            
            if not employee:
                # Поиск по username
                employee = Employee.objects.filter(
                    telegram_username__iexact=username, 
                    is_active=True
                ).first()
                
                if employee and not employee.telegram_id:
                    employee.telegram_id = user_id
                    employee.save()
            
            if employee:
                return {
                    'success': True,
                    'message': (
                        f"✅ Добро пожаловать, {employee.full_name}!\\n"
                        f"🏢 Позиция: {employee.position}\\n"
                        f"🏬 Департамент: {employee.department}\\n"
                        f"📧 Email: {employee.email}\\n\\n"
                        f"🤖 ConnectBot активирован для пользователя @{employee.telegram_username}\\n"
                        f"🆔 Ваш Telegram ID: {user_id}"
                    )
                }
            else:
                return {
                    'success': False,
                    'message': f"❌ Пользователь {username} (ID: {user_id}) не найден в базе данных.\\nОбратитесь к администратору."
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Техническая ошибка: {e}"
            }
    
    def check_user_status(self):
        """Проверить статус пользователя Alexis_yes"""
        try:
            # Поиск пользователя
            user_by_id = Employee.objects.filter(telegram_id=1315776671).first()
            user_by_username = Employee.objects.filter(telegram_username__iexact="Alexis_yes").first()
            
            result = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'search_by_id': None,
                'search_by_username': None,
                'all_users_count': Employee.objects.filter(is_active=True).count()
            }
            
            if user_by_id:
                result['search_by_id'] = {
                    'found': True,
                    'full_name': user_by_id.full_name,
                    'position': user_by_id.position,
                    'telegram_id': user_by_id.telegram_id,
                    'telegram_username': user_by_id.telegram_username,
                    'is_active': user_by_id.is_active,
                    'authorized': user_by_id.authorized
                }
            
            if user_by_username:
                result['search_by_username'] = {
                    'found': True,
                    'full_name': user_by_username.full_name,
                    'position': user_by_username.position,
                    'telegram_id': user_by_username.telegram_id,
                    'telegram_username': user_by_username.telegram_username,
                    'is_active': user_by_username.is_active,
                    'authorized': user_by_username.authorized
                }
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def manual_test(self):
        """Ручной тест авторизации"""
        print("🔍 ДИАГНОСТИКА ПОЛЬЗОВАТЕЛЯ Alexis_yes")
        print("=" * 50)
        
        # Проверяем статус пользователя
        status = self.check_user_status()
        print(f"Время проверки: {status.get('timestamp', 'N/A')}")
        print(f"Всего активных пользователей: {status.get('all_users_count', 0)}")
        
        print("\\n🔎 Поиск по Telegram ID (1315776671):")
        id_result = status.get('search_by_id')
        if id_result and id_result.get('found'):
            print(f"  ✅ Найден: {id_result['full_name']}")
            print(f"     Позиция: {id_result['position']}")
            print(f"     Telegram ID: {id_result['telegram_id']}")
            print(f"     Username: @{id_result['telegram_username']}")
            print(f"     Активен: {id_result['is_active']}")
            print(f"     Авторизован: {id_result['authorized']}")
        else:
            print("  ❌ Не найден по ID")
        
        print("\\n🔎 Поиск по Username (@Alexis_yes):")
        username_result = status.get('search_by_username')
        if username_result and username_result.get('found'):
            print(f"  ✅ Найден: {username_result['full_name']}")
            print(f"     Позиция: {username_result['position']}")
            print(f"     Telegram ID: {username_result['telegram_id']}")
            print(f"     Username: @{username_result['telegram_username']}")
            print(f"     Активен: {username_result['is_active']}")
            print(f"     Авторизован: {username_result['authorized']}")
        else:
            print("  ❌ Не найден по username")
        
        print("\\n🧪 ТЕСТ КОМАНДЫ /start:")
        start_result = self.process_start_command(1315776671, "Alexis_yes")
        print(f"Результат: {'✅ УСПЕХ' if start_result['success'] else '❌ ОТКАЗ'}")
        print(f"Сообщение:")
        print(start_result['message'])
        
        # Сохраняем результат в файл для истории
        with open('bot_diagnostic.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status_check': status,
                'start_command_test': start_result
            }, f, ensure_ascii=False, indent=2)
        
        print("\\n📄 Результаты сохранены в bot_diagnostic.json")

if __name__ == '__main__':
    bot = FileBasedBot()
    bot.manual_test()