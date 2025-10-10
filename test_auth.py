"""
Быстрый тест авторизации пользователя Alexis_yes
"""
import os
import sys
import asyncio
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from employees.utils import AuthManager

async def test_authorization():
    """Тест авторизации"""
    
    # Создаем объект пользователя как в боте
    class TelegramUser:
        def __init__(self, user_id, username, first_name):
            self.id = user_id
            self.username = username  
            self.first_name = first_name
    
    # Данные пользователя Alexis_yes
    telegram_user = TelegramUser(1315776671, "Alexis_yes", "Alexis_yes")
    
    print(f"Тестируем авторизацию для:")
    print(f"  ID: {telegram_user.id}")
    print(f"  Username: {telegram_user.username}")
    print(f"  First name: {telegram_user.first_name}")
    
    try:
        # Тестируем AuthManager
        employee, is_new = await AuthManager.authorize_employee(telegram_user)
        
        if employee:
            print(f"✅ АВТОРИЗАЦИЯ УСПЕШНА!")
            print(f"  Имя: {employee.full_name}")
            print(f"  Позиция: {employee.position}")
            print(f"  Email: {employee.email}")
            print(f"  Telegram ID: {employee.telegram_id}")
            print(f"  Telegram Username: {employee.telegram_username}")
            print(f"  Активен: {employee.is_active}")
            print(f"  Авторизован: {employee.authorized}")
            print(f"  Новая авторизация: {is_new}")
        else:
            print("❌ АВТОРИЗАЦИЯ ОТКЛОНЕНА!")
            print("Пользователь не найден в базе данных")
            
    except Exception as e:
        print(f"💥 ОШИБКА АВТОРИЗАЦИИ: {e}")

if __name__ == '__main__':
    asyncio.run(test_authorization())