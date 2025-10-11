#!/usr/bin/env python
"""
Интерактивное тестирование функции управления интересами в ConnectBot
"""
import os
import sys
import asyncio
import logging
from unittest.mock import Mock, AsyncMock

# Добавляем корневую папку проекта в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from telegram import Update, User, CallbackQuery, Message, Chat
from telegram.ext import ContextTypes
from employees.models import Employee, Interest, EmployeeInterest
from bots.menu_manager import MenuManager
from employees.utils import PreferenceManager

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InterestsBotSimulator:
    """Симуляция работы бота с интересами"""
    
    def __init__(self):
        self.context = None
        self.employee = None
    
    async def setup_test_employee(self):
        """Подготовка тестового сотрудника"""
        try:
            # Ищем сотрудника с Telegram ID (авторизованного)
            self.employee = await Employee.objects.filter(
                telegram_id__isnull=False
            ).select_related('department', 'business_center').afirst()
            
            if not self.employee:
                # Берем любого сотрудника и добавляем ему telegram_id
                self.employee = await Employee.objects.select_related(
                    'department', 'business_center'
                ).afirst()
                
                if self.employee:
                    self.employee.telegram_id = 123456789  # Тестовый ID
                    self.employee.telegram_username = "test_user"
                    await Employee.objects.filter(id=self.employee.id).aupdate(
                        telegram_id=123456789,
                        telegram_username="test_user"
                    )
            
            if self.employee:
                logger.info(f"✅ Подготовлен тестовый сотрудник: {self.employee.full_name}")
                return True
            else:
                logger.error("❌ Не найден подходящий сотрудник для тестирования")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка подготовки сотрудника: {e}")
            return False
    
    def create_mock_update(self, callback_data=None, message_text=None):
        """Создание мок-обновления"""
        # Создаем мок пользователя
        user = Mock(spec=User)
        user.id = self.employee.telegram_id
        user.username = self.employee.telegram_username
        user.first_name = self.employee.full_name.split()[0]
        
        # Создаем мок чата
        chat = Mock(spec=Chat)
        chat.id = self.employee.telegram_id
        chat.type = 'private'
        
        # Создаем мок обновления
        update = Mock(spec=Update)
        update.effective_user = user
        update.effective_chat = chat
        
        if callback_data:
            # Для callback query
            callback_query = Mock(spec=CallbackQuery)
            callback_query.from_user = user
            callback_query.data = callback_data
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            update.callback_query = callback_query
        
        if message_text:
            # Для сообщения
            message = Mock(spec=Message)
            message.from_user = user
            message.chat = chat
            message.text = message_text
            message.reply_text = AsyncMock()
            update.message = message
        
        return update
    
    async def simulate_interests_menu(self):
        """Симуляция открытия меню интересов"""
        logger.info("📱 Симуляция открытия меню 'Мои интересы'...")
        
        try:
            # Создаем меню интересов
            menu_data = await MenuManager.create_interests_menu(self.employee)
            
            logger.info("✅ Меню интересов создано!")
            logger.info("📝 Содержимое меню:")
            logger.info("-" * 50)
            print(menu_data['text'])
            logger.info("-" * 50)
            
            # Показываем доступные кнопки
            keyboard = menu_data['reply_markup'].inline_keyboard
            logger.info(f"🔘 Доступные кнопки ({len(keyboard)}):")
            
            for i, row in enumerate(keyboard):
                for button in row:
                    logger.info(f"  {i+1}. {button.text} -> {button.callback_data}")
            
            return menu_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания меню интересов: {e}")
            return None
    
    async def simulate_toggle_interest(self, interest_code):
        """Симуляция переключения интереса"""
        logger.info(f"🔄 Симуляция переключения интереса: {interest_code}")
        
        try:
            # Получаем текущие интересы
            current_interests = await PreferenceManager.get_employee_interests(self.employee)
            active_codes = [ei.interest.code for ei in current_interests if ei.is_active]
            
            # Переключаем интерес
            if interest_code in active_codes:
                # Отключаем
                active_codes.remove(interest_code)
                action = "отключен"
            else:
                # Включаем
                active_codes.append(interest_code)
                action = "включен"
            
            # Обновляем интересы
            success = await PreferenceManager.update_employee_interests(
                self.employee, active_codes
            )
            
            if success:
                logger.info(f"✅ Интерес '{interest_code}' {action}")
                
                # Получаем обновленное меню
                updated_menu = await MenuManager.create_interests_menu(self.employee)
                return updated_menu
            else:
                logger.error(f"❌ Ошибка переключения интереса '{interest_code}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка симуляции переключения интереса: {e}")
            return None
    
    async def simulate_save_interests(self):
        """Симуляция сохранения интересов"""
        logger.info("💾 Симуляция сохранения интересов...")
        
        try:
            # Получаем текущие активные интересы
            current_interests = await PreferenceManager.get_employee_interests(self.employee)
            active_interests = [ei for ei in current_interests if ei.is_active]
            
            logger.info("✅ Интересы сохранены!")
            logger.info(f"📊 Активных подписок: {len(active_interests)}")
            
            for ei in active_interests:
                logger.info(f"  • {ei.interest.emoji} {ei.interest.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения интересов: {e}")
            return False
    
    async def simulate_disable_all(self):
        """Симуляция отключения всех интересов"""
        logger.info("🚫 Симуляция отключения всех интересов...")
        
        try:
            success = await PreferenceManager.disable_all_interests(self.employee)
            
            if success:
                logger.info("✅ Все интересы отключены!")
                
                # Получаем обновленное меню
                updated_menu = await MenuManager.create_interests_menu(self.employee)
                return updated_menu
            else:
                logger.error("❌ Ошибка отключения всех интересов")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка симуляции отключения всех интересов: {e}")
            return None

async def main():
    """Основная функция интерактивного тестирования"""
    logger.info("🚀 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ИНТЕРЕСАМИ")
    logger.info("=" * 60)
    
    simulator = InterestsBotSimulator()
    
    # Подготовка
    if not await simulator.setup_test_employee():
        logger.error("❌ Не удалось подготовить тестового сотрудника")
        return
    
    # Тестирование
    logger.info("\n1️⃣ Открываем меню 'Мои интересы'")
    menu_data = await simulator.simulate_interests_menu()
    
    if not menu_data:
        logger.error("❌ Не удалось создать меню")
        return
    
    # Получаем доступные интересы для тестирования
    all_interests = await PreferenceManager.get_all_interests()
    
    if len(all_interests) >= 2:
        # Тестируем переключение интересов
        test_interest = all_interests[0].code
        
        logger.info(f"\n2️⃣ Включаем интерес: {test_interest}")
        updated_menu = await simulator.simulate_toggle_interest(test_interest)
        
        if updated_menu:
            logger.info("✅ Меню обновлено после включения интереса")
        
        logger.info(f"\n3️⃣ Отключаем интерес: {test_interest}")
        await simulator.simulate_toggle_interest(test_interest)
        
        # Включаем несколько интересов
        logger.info("\n4️⃣ Включаем несколько интересов для демонстрации")
        for interest in all_interests[:3]:
            await simulator.simulate_toggle_interest(interest.code)
        
        # Сохраняем интересы
        logger.info("\n5️⃣ Сохраняем текущие настройки")
        await simulator.simulate_save_interests()
        
        # Отключаем все
        logger.info("\n6️⃣ Отключаем все интересы")
        await simulator.simulate_disable_all()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    logger.info("\n💡 Для тестирования в реальном боте:")
    logger.info("   1. Убедитесь, что бот запущен")
    logger.info("   2. Найдите бота в Telegram")
    logger.info("   3. Отправьте /start")
    logger.info("   4. Нажмите 'Мои интересы' в главном меню")
    logger.info("   5. Протестируйте переключение интересов")

if __name__ == "__main__":
    asyncio.run(main())