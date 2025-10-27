"""
Тестовая версия бота с простым polling и лучшей обработкой ошибок
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
import time

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from asgiref.sync import sync_to_async

from employees.utils import AuthManager, PreferenceManager
from employees.redis_utils import RedisManager
from bots.menu_manager import MenuManager
from bots.utils.message_utils import reply_with_footer

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Отключаем избыточные логи
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


class ConnectBotTest:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()
        self.is_running = False
        
        logger.info(f"Инициализация бота. Redis: {'ДА' if self.redis_available else 'НЕТ'}")
    
    async def test_bot_connection(self):
        """Тестирование подключения к боту"""
        try:
            bot = Bot(token=self.token)
            me = await bot.get_me()
            logger.info(f"Бот подключен: @{me.username} ({me.first_name})")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к боту: {e}")
            return False
    
    async def get_user_session(self, user_id: int) -> dict:
        """Получить сессию пользователя"""
        if not self.redis_available:
            return {}
        
        try:
            session_data = RedisManager.get_bot_session(user_id)
            return session_data or {}
        except Exception as e:
            logger.error(f"Ошибка сессии {user_id}: {e}")
            return {}
    
    async def update_user_session(self, user_id: int, session_data: dict):
        """Обновить сессию пользователя"""
        if not self.redis_available:
            return
        
        try:
            current_session = await self.get_user_session(user_id)
            current_session.update(session_data)
            RedisManager.store_bot_session(user_id, current_session)
        except Exception as e:
            logger.error(f"Ошибка обновления сессии {user_id}: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name or str(user_id)
        
        logger.info(f"START команда от {username} (ID: {user_id})")
        
        try:
            # Проверяем авторизацию
            auth_manager = AuthManager()
            is_authorized = await sync_to_async(auth_manager.is_user_authorized)(user_id, username)
            
            if not is_authorized:
                logger.warning(f"Неавторизован: {username}")
                await reply_with_footer(update, f"Доступ запрещен для {username}\\nОбратитесь к администратору.")
                return
            
            # Получаем данные пользователя
            employee_data = await sync_to_async(auth_manager.get_user_data)(user_id)
            
            if employee_data:
                # Сохраняем сессию
                session_data = {
                    'employee_id': employee_data['id'],
                    'username': employee_data['username'],
                    'role': employee_data['role']
                }
                await self.update_user_session(user_id, session_data)
                
                logger.info(f"Авторизован: {username} -> {employee_data['role']}")
                
                response = (
                    f"Привет, {employee_data['username']}!\\n"
                    f"Роль: {employee_data['role']}\\n\\n"
                    "ConnectBot готов к работе!\\n"
                    "Доступные команды:\\n"
                    "/menu - основное меню\\n"
                    "/preferences - настройки\\n"
                    "/status - статус бота"
                )
                
                await reply_with_footer(update, response)
            else:
                await reply_with_footer(update, "Ошибка получения данных пользователя")
                
        except Exception as e:
            logger.error(f"Ошибка в /start: {e}")
            await reply_with_footer(update, "Техническая ошибка")
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        user = update.effective_user
        logger.info(f"MENU от {user.username}")
        
        try:
            session_data = await self.get_user_session(user.id)
            
            if not session_data:
                await reply_with_footer(update, "Выполните /start для авторизации")
                return
            
            menu_manager = MenuManager()
            menu_data = await sync_to_async(menu_manager.get_main_menu)(
                session_data.get('employee_id'),
                session_data.get('role')
            )
            
            if isinstance(menu_data, dict) and menu_data.get('reply_markup'):
                await update.message.reply_text(**menu_data)
            else:
                await reply_with_footer(update, menu_data.get('text') if isinstance(menu_data, dict) else menu_data)
            
        except Exception as e:
            logger.error(f"Ошибка меню: {e}")
            await reply_with_footer(update, "Ошибка загрузки меню")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда статуса бота"""
        user = update.effective_user
        logger.info(f"STATUS от {user.username}")
        
        try:
            # Проверяем статус компонентов
            redis_status = "OK" if self.redis_available else "НЕТ"
            
            # Проверяем количество пользователей
            auth_manager = AuthManager()
            user_count = await sync_to_async(lambda: auth_manager.get_authorized_users_count())()
            
            status_text = (
                f"Статус ConnectBot:\\n\\n"
                f"Redis: {redis_status}\\n"
                f"Авторизованных пользователей: {user_count}\\n"
                f"Время: {time.strftime('%H:%M:%S')}\\n"
                f"Бот работает: {'ДА' if self.is_running else 'НЕТ'}"
            )
            
            await reply_with_footer(update, status_text)
            
        except Exception as e:
            logger.error(f"Ошибка статуса: {e}")
            await reply_with_footer(update, "Ошибка получения статуса")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        
        try:
            await query.answer()
            
            session_data = await self.get_user_session(update.effective_user.id)
            
            if not session_data:
                await query.edit_message_text("Сессия истекла")
                return
            
            callback_data = query.data
            logger.info(f"CALLBACK: {callback_data}")
            
            # Простая обработка callback
            if callback_data == "test":
                await query.edit_message_text("Тест успешен!")
            else:
                await query.edit_message_text(f"Обработан callback: {callback_data}")
                
        except Exception as e:
            logger.error(f"Ошибка callback: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных сообщений"""
        user = update.effective_user
        text = update.message.text
        
        logger.info(f"MSG от {user.username}: {text}")
        
        response = (
            f"Сообщение получено: {text}\\n\\n"
            "Команды:\\n"
            "/menu - меню\\n"
            "/status - статус\\n"
            "/preferences - настройки"
        )
        
        await reply_with_footer(update, response)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        error = context.error
        error_type = type(error).__name__
        
        # Игнорируем сетевые ошибки
        if any(net_err in error_type for net_err in ["TimedOut", "NetworkError", "RetryAfter"]):
            logger.debug(f"Сетевая ошибка (игнорируем): {error_type}")
            return
        
        logger.error(f"Ошибка бота: {error_type}: {error}")
        
        # Не отправляем сообщения при ошибках сети
        if update and hasattr(update, 'effective_message') and "TimedOut" not in str(error):
            try:
                await reply_with_footer(update, "Произошла ошибка")
            except:
                pass
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        logger.info("Настройка обработчиков")
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.menu))
        self.application.add_handler(CommandHandler("status", self.status))
        
        # Callback и сообщения
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Обработчики готовы")
    
    async def run_with_retry(self):
        """Запуск с повторными попытками"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Попытка запуска #{retry_count + 1}")
                
                # Тестируем соединение
                if await self.test_bot_connection():
                    logger.info("Соединение с ботом установлено")
                else:
                    raise Exception("Не удалось подключиться к боту")
                
                self.is_running = True
                
                # Запускаем polling с короткими таймаутами
                await self.application.initialize()
                await self.application.start()
                
                logger.info("Запуск polling...")
                
                # Запускаем updater
                updater = self.application.updater
                await updater.start_polling(
                    poll_interval=1.0,  # Короткий интервал
                    timeout=10,         # Короткий таймаут
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                
                logger.info("Bot запущен успешно!")
                
                # Бесконечное ожидание (пока не будет Ctrl+C)
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки")
                finally:
                    # Корректная остановка
                    await updater.stop()
                    await self.application.stop()
                    await self.application.shutdown()
                
                break  # Успешный запуск
                
            except KeyboardInterrupt:
                logger.info("Остановка по Ctrl+C")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Ошибка запуска (попытка {retry_count}): {e}")
                
                if retry_count < max_retries:
                    wait_time = min(10, 2 ** retry_count)  # Экспоненциальная задержка
                    logger.info(f"Повтор через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Исчерпаны попытки запуска")
                    break
            finally:
                self.is_running = False
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск ConnectBot (тестовая версия)")
        
        try:
            # Создаем приложение
            self.application = Application.builder().token(self.token).build()
            self.setup_handlers()
            
            # Запускаем с повторными попытками
            asyncio.run(self.run_with_retry())
            
        except KeyboardInterrupt:
            logger.info("Остановка бота")
        except Exception as e:
            logger.error(f"Фатальная ошибка: {e}")


if __name__ == '__main__':
    bot = ConnectBotTest()
    bot.run()