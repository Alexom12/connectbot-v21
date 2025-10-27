"""
Минимальная стабильная версия бота без SSL модификаций
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
        logging.FileHandler('bot_minimal.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Отключаем предупреждения httpx о SSL
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class ConnectBotMinimal:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()
        
        if self.redis_available:
            logger.info("Redis доступен")
        else:
            logger.warning("Redis недоступен")
    
    async def get_user_session(self, user_id: int) -> dict:
        """Получить сессию пользователя"""
        if not self.redis_available:
            return {}
        
        try:
            session_data = RedisManager.get_bot_session(user_id)
            return session_data or {}
        except Exception as e:
            logger.error(f"Ошибка сессии пользователя {user_id}: {e}")
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
    
    async def clear_user_session(self, user_id: int):
        """Очистить сессию пользователя"""
        if not self.redis_available:
            return
        
        try:
            RedisManager.clear_bot_session(user_id)
        except Exception as e:
            logger.error(f"Ошибка очистки сессии {user_id}: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        logger.info(f"START: {username} (ID: {user_id})")
        
        try:
            # Проверяем авторизацию пользователя
            auth_manager = AuthManager()
            is_authorized = await sync_to_async(auth_manager.is_user_authorized)(user_id, username)

            if not is_authorized:
                logger.warning(f"Неавторизован: {username}")
                await reply_with_footer(update, f"Извините, {username}, у вас нет доступа к этому боту.\nОбратитесь к администратору.")
                return
            
            # Очищаем и обновляем сессию
            await self.clear_user_session(user_id)
            employee_data = await sync_to_async(auth_manager.get_user_data)(user_id)
            
            if employee_data:
                session_data = {
                    'employee_id': employee_data['id'],
                    'username': employee_data['username'],
                    'role': employee_data['role']
                }
                await self.update_user_session(user_id, session_data)
                
                logger.info(f"Авторизован: {username} как {employee_data['role']}")
                
                response = (
                    f"Привет, {employee_data['username']}!\\n"
                    f"Роль: {employee_data['role']}\\n\\n"
                    "Добро пожаловать в ConnectBot!\\n"
                    "Команды: /menu /preferences"
                )
                
                await reply_with_footer(update, response)
            else:
                logger.error(f"Нет данных пользователя: {username}")
                await reply_with_footer(update, "Ошибка авторизации. Попробуйте позже.")
                
        except Exception as e:
            logger.error(f"Ошибка /start: {e}")
            await self.safe_reply(update.message, "Техническая ошибка. Попробуйте позже.")
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        user = update.effective_user
        logger.info(f"MENU: {user.username}")
        
        try:
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await reply_with_footer(update, "Сессия истекла. Используйте /start")
                return
            
            menu_manager = MenuManager()
            menu_data = await sync_to_async(menu_manager.get_main_menu)(
                session_data.get('employee_id'),
                session_data.get('role')
            )
            
            # menu_data may include reply_markup already; if not, use footer helper
            if isinstance(menu_data, dict) and menu_data.get('reply_markup'):
                await update.message.reply_text(**menu_data)
            else:
                # Prefer reply_with_footer for consistent bottom keyboard
                await reply_with_footer(update, menu_data.get('text') if isinstance(menu_data, dict) else menu_data)
            
        except Exception as e:
            logger.error(f"Ошибка меню: {e}")
            await self.safe_reply(update.message, "Ошибка загрузки меню.")
    
    async def preferences(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /preferences"""
        user = update.effective_user
        logger.info(f"PREFS: {user.username}")
        
        try:
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await reply_with_footer(update, "Сессия истекла. Используйте /start")
                return
            
            preference_manager = PreferenceManager()
            preferences_data = await sync_to_async(preference_manager.get_user_preferences_menu)(
                session_data.get('employee_id')
            )
            
            if isinstance(preferences_data, dict) and preferences_data.get('reply_markup'):
                await update.message.reply_text(**preferences_data)
            else:
                await reply_with_footer(update, preferences_data.get('text') if isinstance(preferences_data, dict) else preferences_data)
            
        except Exception as e:
            logger.error(f"Ошибка настроек: {e}")
            await self.safe_reply(update.message, "Ошибка загрузки настроек.")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        
        try:
            await query.answer()
            
            user_id = update.effective_user.id
            session_data = await self.get_user_session(user_id)
            
            if not session_data:
                await query.edit_message_text("Сессия истекла. Используйте /start")
                return
            
            callback_data = query.data
            logger.info(f"CALLBACK: {query.from_user.username}: {callback_data}")
            
            if callback_data == "refresh_menu":
                menu_manager = MenuManager()
                menu_data = await sync_to_async(menu_manager.get_main_menu)(
                    session_data.get('employee_id'),
                    session_data.get('role')
                )
                await query.edit_message_text(**menu_data)
            
            elif callback_data.startswith("coffee_"):
                coffee_type = callback_data.replace("coffee_", "")
                response = (
                    f"Заказ кофе '{coffee_type}' принят!\\n"
                    f"Пользователь: {session_data.get('username')}"
                )
                await query.edit_message_text(response)
            
            elif callback_data.startswith("pref_"):
                pref_action = callback_data.replace("pref_", "")
                response = (
                    f"Настройка '{pref_action}' изменена.\\n"
                    f"Пользователь: {session_data.get('username')}"
                )
                await query.edit_message_text(response)
            
            else:
                await query.edit_message_text("Неизвестная команда.")
                
        except Exception as e:
            logger.error(f"Ошибка callback: {e}")
            try:
                if query and hasattr(query, 'edit_message_text'):
                    await query.edit_message_text("Ошибка обработки команды.")
            except:
                pass
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"MSG: {user.username}: {message_text}")
        
        response = (
            f"Сообщение получено: {message_text}\\n"
            "Команды: /menu /preferences"
        )
        
        await self.safe_reply(update.message, response)
    
    async def safe_reply(self, message, text):
        """Безопасная отправка ответа с обработкой ошибок"""
        try:
            # Prefer reply_with_footer when possible to attach persistent footer
            try:
                fake_update = type('U', (), {'message': message, 'effective_message': message})()
                await reply_with_footer(fake_update, text)
            except Exception:
                await message.reply_text(text)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        error = context.error
        error_str = str(error)
        
        # Логируем только критичные ошибки, игнорируем сетевые проблемы
        if any(err_type in error_str for err_type in ["TimedOut", "ConnectTimeout", "NetworkError", "BadRequest"]):
            logger.warning(f"Сетевая ошибка (игнорируем): {error}")
            return
        
        logger.error(f"Критическая ошибка: {error}")
        
        # Не пытаемся отправлять сообщения при сетевых проблемах
        if update and hasattr(update, 'effective_message') and update.effective_message:
            try:
                await reply_with_footer(update, "Произошла ошибка. Попробуйте позже.")
            except:
                try:
                    await reply_with_footer(update, "Произошла ошибка. Попробуйте позже.")
                except:
                    pass  # Игнорируем ошибки отправки сообщений об ошибках
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        logger.info("Настройка обработчиков")
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("menu", self.menu))
        self.application.add_handler(CommandHandler("preferences", self.preferences))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Обработчики готовы")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск ConnectBot (минимальная версия)")
        
        try:
            # Создаем стандартное приложение без модификаций
            self.application = Application.builder().token(self.token).build()
            
            self.setup_handlers()
            
            logger.info("Начинаем polling...")
            logger.info(f"Токен: {self.token[:10]}...")
            
            # Запуск с базовыми настройками
            self.application.run_polling(
                poll_interval=3.0,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except KeyboardInterrupt:
            logger.info("Остановка бота пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise


if __name__ == '__main__':
    try:
        bot = ConnectBotMinimal()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")