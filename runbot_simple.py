"""
Простая исправленная версия бота с увеличенными таймаутами
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from asgiref.sync import sync_to_async
import httpx

from employees.utils import AuthManager, PreferenceManager
from employees.redis_utils import RedisManager
from bots.menu_manager import MenuManager

# Настройка логирования без эмодзи для избежания проблем с кодировкой
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConnectBotSimple:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()
        
        if self.redis_available:
            logger.info("Redis доступен, включено кеширование сессий")
        else:
            logger.warning("Redis недоступен, кеширование сессий отключено")
    
    def create_custom_request(self):
        """Создает HTTPXRequest с увеличенными таймаутами"""
        # Настраиваем httpx клиент с увеличенными таймаутами
        httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=60.0,  # 60 секунд на подключение
                read=60.0,     # 60 секунд на чтение
                write=60.0,    # 60 секунд на запись
                pool=60.0      # 60 секунд для пула соединений
            ),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=60
            ),
            # Добавляем retry логику
            transport=httpx.AsyncHTTPTransport(retries=3)
        )
        
        return HTTPXRequest(client=httpx_client)
    
    async def get_user_session(self, user_id: int) -> dict:
        """Получить сессию пользователя"""
        if not self.redis_available:
            return {}
        
        try:
            session_data = RedisManager.get_bot_session(user_id)
            return session_data or {}
        except Exception as e:
            logger.error(f"Ошибка получения сессии для пользователя {user_id}: {e}")
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
            logger.error(f"Ошибка обновления сессии для пользователя {user_id}: {e}")
    
    async def clear_user_session(self, user_id: int):
        """Очистить сессию пользователя"""
        if not self.redis_available:
            return
        
        try:
            RedisManager.clear_bot_session(user_id)
        except Exception as e:
            logger.error(f"Ошибка очистки сессии для пользователя {user_id}: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        logger.info(f"Команда /start от пользователя {username} (ID: {user_id})")
        
        try:
            # Проверяем авторизацию пользователя
            auth_manager = AuthManager()
            is_authorized = await sync_to_async(auth_manager.is_user_authorized)(user_id, username)
            
            if not is_authorized:
                logger.warning(f"Неавторизованный пользователь: {username} (ID: {user_id})")
                await update.message.reply_text(
                    f"Извините, {username}, у вас нет доступа к этому боту.\\n"
                    "Обратитесь к администратору для получения доступа."
                )
                return
            
            # Очищаем сессию пользователя
            await self.clear_user_session(user_id)
            
            # Получаем данные пользователя
            employee_data = await sync_to_async(auth_manager.get_user_data)(user_id)
            
            if employee_data:
                # Обновляем сессию
                session_data = {
                    'employee_id': employee_data['id'],
                    'username': employee_data['username'],
                    'role': employee_data['role']
                }
                await self.update_user_session(user_id, session_data)
                
                logger.info(f"Пользователь {username} успешно авторизован как {employee_data['role']}")
                
                await update.message.reply_text(
                    f"Привет, {employee_data['username']}!\\n"
                    f"Ваша роль: {employee_data['role']}\\n\\n"
                    "Добро пожаловать в ConnectBot!\\n"
                    "Используйте /menu для доступа к основному меню."
                )
            else:
                logger.error(f"Ошибка получения данных пользователя {username}")
                await update.message.reply_text(
                    "Произошла ошибка при авторизации. Попробуйте позже или обратитесь к администратору."
                )
                
        except Exception as e:
            logger.error(f"Ошибка в команде /start: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "Произошла техническая ошибка. Попробуйте позже."
                )
            except Exception as reply_error:
                logger.error(f"Ошибка отправки сообщения об ошибке: {reply_error}")
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        try:
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await update.message.reply_text("Сессия истекла. Введите /start для повторной авторизации.")
                return
            
            # Получаем меню через MenuManager
            menu_manager = MenuManager()
            menu_data = await sync_to_async(menu_manager.get_main_menu)(
                session_data.get('employee_id'),
                session_data.get('role')
            )
            
            await update.message.reply_text(**menu_data)
            
        except Exception as e:
            logger.error(f"Ошибка показа главного меню: {e}", exc_info=True)
            try:
                await update.message.reply_text("Ошибка загрузки меню. Попробуйте позже.")
            except Exception as reply_error:
                logger.error(f"Ошибка отправки сообщения об ошибке меню: {reply_error}")
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        user = update.effective_user
        logger.info(f"Команда /menu от пользователя {user.username} (ID: {user.id})")
        
        try:
            await self.show_main_menu(update, context)
        except Exception as e:
            logger.error(f"Ошибка в команде /menu: {e}", exc_info=True)
    
    async def preferences(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /preferences"""
        user = update.effective_user
        logger.info(f"Команда /preferences от пользователя {user.username} (ID: {user.id})")
        
        try:
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await update.message.reply_text("Сессия истекла. Введите /start для повторной авторизации.")
                return
            
            # Получаем настройки через PreferenceManager
            preference_manager = PreferenceManager()
            preferences_data = await sync_to_async(preference_manager.get_user_preferences_menu)(
                session_data.get('employee_id')
            )
            
            await update.message.reply_text(**preferences_data)
            
        except Exception as e:
            logger.error(f"Ошибка в команде /preferences: {e}", exc_info=True)
            try:
                await update.message.reply_text("Ошибка загрузки настроек. Попробуйте позже.")
            except Exception as reply_error:
                logger.error(f"Ошибка отправки сообщения об ошибке настроек: {reply_error}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        
        try:
            await query.answer()
            
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await query.edit_message_text("Сессия истекла. Введите /start для повторной авторизации.")
                return
            
            callback_data = query.data
            logger.info(f"Callback от пользователя {query.from_user.username}: {callback_data}")
            
            if callback_data == "refresh_menu":
                menu_manager = MenuManager()
                menu_data = await sync_to_async(menu_manager.get_main_menu)(
                    session_data.get('employee_id'),
                    session_data.get('role')
                )
                await query.edit_message_text(**menu_data)
            
            elif callback_data.startswith("coffee_"):
                # Обработка кофейных команд
                coffee_type = callback_data.replace("coffee_", "")
                await self.handle_coffee_order(query, coffee_type, session_data)
            
            elif callback_data.startswith("pref_"):
                # Обработка настроек
                pref_action = callback_data.replace("pref_", "")
                await self.handle_preference_change(query, pref_action, session_data)
            
            else:
                await query.edit_message_text("Неизвестная команда.")
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
            try:
                if query:
                    await query.edit_message_text("Произошла ошибка. Попробуйте позже.")
            except Exception as edit_error:
                logger.error(f"Ошибка редактирования сообщения: {edit_error}")
    
    async def handle_coffee_order(self, query, coffee_type: str, session_data: dict):
        """Обработка заказа кофе"""
        try:
            await query.edit_message_text(
                f"Заказ кофе '{coffee_type}' обрабатывается...\\n"
                f"Пользователь: {session_data.get('username')}\\n"
                f"Роль: {session_data.get('role')}"
            )
        except Exception as e:
            logger.error(f"Ошибка обработки заказа кофе: {e}")
    
    async def handle_preference_change(self, query, pref_action: str, session_data: dict):
        """Обработка изменения настроек"""
        try:
            await query.edit_message_text(
                f"Настройка '{pref_action}' изменена.\\n"
                f"Пользователь: {session_data.get('username')}"
            )
        except Exception as e:
            logger.error(f"Ошибка изменения настроек: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Сообщение от {user.username}: {message_text}")
        
        try:
            await update.message.reply_text(
                f"Получено сообщение: {message_text}\\n"
                "Используйте /menu для доступа к функциям бота."
            )
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        error = context.error
        logger.error(f"Произошла ошибка: {error}", exc_info=True)
        
        # Не пытаемся отправить сообщение об ошибке, если это проблема с сетью
        if "TimedOut" in str(error) or "ConnectTimeout" in str(error):
            logger.warning("Проблема с сетевым подключением к Telegram")
            return
        
        if update and hasattr(update, 'effective_message') and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "Произошла техническая ошибка. Команда разработки уведомлена."
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения об ошибке: {e}")
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        logger.info("Настройка обработчиков...")
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.menu))
        self.application.add_handler(CommandHandler("preferences", self.preferences))
        
        # Callback запросы
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Обработчики настроены")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск ConnectBot с увеличенными таймаутами...")
        
        try:
            # Создаем приложение с кастомным request объектом
            custom_request = self.create_custom_request()
            
            self.application = Application.builder().token(self.token).request(custom_request).build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            logger.info("Приложение настроено, начинаем polling...")
            logger.info(f"Используется токен: {self.token[:10]}...")
            
            # Запускаем бота с увеличенными таймаутами
            self.application.run_polling(
                poll_interval=5.0,   # Интервал опроса 5 секунд (больше обычного)
                timeout=60,          # Таймаут 60 секунд
                read_timeout=60,     # Таймаут чтения 60 секунд
                write_timeout=60,    # Таймаут записи 60 секунд
                connect_timeout=60,  # Таймаут подключения 60 секунд
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Пропускаем старые сообщения при запуске
            )
            
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    bot = ConnectBotSimple()
    bot.run()