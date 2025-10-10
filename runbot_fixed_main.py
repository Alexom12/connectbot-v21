"""
Исправленная версия основного Telegram бота ConnectBot 
- Устраняет конфликты getUpdates
- Добавляет управление состоянием подключений
- Улучшает обработку ошибок
"""
import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
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

logger = logging.getLogger(__name__)


class ImprovedConnectBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()
        self.running = False
        
        # Добавляем обработку сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if self.redis_available:
            logger.info("✅ Redis доступен, включено кеширование сессий")
        else:
            logger.warning("⚠️  Redis недоступен, кеширование сессий отключено")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, останавливаем бот...")
        self.running = False
        
        if self.application and self.application.updater:
            asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Корректное завершение работы бота"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            logger.info("Бот корректно остановлен")
        except Exception as e:
            logger.error(f"Ошибка при завершении: {e}")
    
    async def get_user_session(self, user_id: int) -> dict:
        """Получить сессию пользователя"""
        if not self.redis_available:
            return {}
        
        session_data = RedisManager.get_bot_session(user_id)
        return session_data or {}
    
    async def update_user_session(self, user_id: int, session_data: dict):
        """Обновить сессию пользователя"""
        if not self.redis_available:
            return
        
        current_session = await self.get_user_session(user_id)
        current_session.update(session_data)
        RedisManager.store_bot_session(user_id, current_session)
    
    async def clear_user_session(self, user_id: int):
        """Очистить сессию пользователя"""
        if not self.redis_available:
            return
        
        RedisManager.clear_bot_session(user_id)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        try:
            # Авторизация сотрудника
            employee, is_new = await AuthManager.authorize_employee(user)
            
            if employee:
                # Инициализируем/обновляем сессию пользователя
                await self.update_user_session(user.id, {
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'authorized': True,
                    'last_command': '/start'
                })
                
                # Отправляем приветственное сообщение
                welcome_message = await AuthManager.get_welcome_message(employee)
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
                
                # Если новая авторизация, предлагаем настроить предпочтения
                if is_new:
                    await self.update_user_session(user.id, {'setup_step': 'preferences'})
                    await self.show_preferences_setup(update, context, employee)
                else:
                    # Показываем главное меню
                    await self.show_main_menu(update, context)
                    
            else:
                # Пользователь не найден - очищаем сессию
                await self.clear_user_session(user.id)
                error_message = await AuthManager.get_unauthorized_message()
                formatted_message = error_message.format(username=user.username or 'ваш_username')
                await update.message.reply_text(formatted_message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Ошибка в команде /start: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при авторизации. Попробуйте позже или обратитесь к администратору."
            )
    
    async def show_preferences_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee):
        """Настройка предпочтений при первой авторизации"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("🎯 Настроить интересы", callback_data="setup_preferences")],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_setup")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📋 *Давайте настроим ваши предпочтения!*\n\n"
            "Выберите активности, уведомления о которых хотите получать. "
            "Это поможет нам предлагать вам релевантные мероприятия.\n\n"
            "Вы всегда сможете изменить настройки через команду /preferences",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        menu_data = await MenuManager.create_main_menu()
        
        if update.message:
            await update.message.reply_text(**menu_data)
        else:
            await update.callback_query.edit_message_text(**menu_data)
    
    async def show_profile_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee):
        """Показать меню профиля"""
        menu_data = await MenuManager.create_profile_menu(employee)
        await update.callback_query.edit_message_text(**menu_data)
    
    async def show_interests_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee):
        """Показать меню интересов"""
        menu_data = await MenuManager.create_interests_menu(employee)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(**menu_data)
        else:
            await update.message.reply_text(**menu_data)
    
    async def preferences(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /preferences"""
        user = update.effective_user
        
        try:
            employee, _ = await AuthManager.authorize_employee(user)
            if not employee:
                error_message = await AuthManager.get_unauthorized_message()
                formatted_message = error_message.format(username=user.username or 'ваш_username')
                await update.message.reply_text(formatted_message, parse_mode='Markdown')
                return
            
            await self.show_interests_menu(update, context, employee)
            
        except Exception as e:
            logger.error(f"Ошибка в команде /preferences: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        await self.show_main_menu(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback-запросов с улучшенной обработкой ошибок"""
        query = update.callback_query
        
        try:
            await query.answer()
            callback_data = query.data
            user = query.from_user
            
            # Проверяем сессию пользователя
            session_data = await self.get_user_session(user.id)
            
            # Авторизуем сотрудника
            employee, _ = await AuthManager.authorize_employee(user)
            if not employee:
                await self.clear_user_session(user.id)
                await query.edit_message_text(
                    "❌ Ваша сессия устарела. Используйте /start для повторной авторизации."
                )
                return
            
            # Обновляем сессию
            await self.update_user_session(user.id, {
                'last_callback': callback_data,
                'last_action_time': str(asyncio.get_event_loop().time())
            })
            
            # Обрабатываем навигацию по меню
            if callback_data == "menu_profile":
                await self.show_profile_menu(update, context, employee)
                
            elif callback_data == "menu_interests":
                await self.show_interests_menu(update, context, employee)
                
            elif callback_data == "setup_preferences":
                await self.show_interests_menu(update, context, employee)
                
            elif callback_data == "skip_setup":
                await query.edit_message_text(
                    "✅ Отлично! Вы можете настроить интересы позже через команду /preferences\n\n"
                    "Переходим в главное меню...",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(2)
                await self.show_main_menu(update, context)
                
            # Обработка кнопки Назад
            elif callback_data.startswith("back_"):
                target = callback_data.replace("back_", "")
                if target == "main":
                    await self.show_main_menu(update, context)
                elif target == "profile":
                    await self.show_profile_menu(update, context, employee)
                    
            else:
                await query.edit_message_text(
                    "🔧 Функция в разработке...\n\n"
                    "Скоро здесь появится новый функционал! 🚀",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            try:
                await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")
            except:
                # Если не удалось отредактировать сообщение, попробуем ответить
                try:
                    await query.answer("❌ Произошла ошибка", show_alert=True)
                except:
                    pass  # Игнорируем ошибки при уведомлении
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "🤖 *ConnectBot - Помощь*\n\n"
            "📋 *Доступные команды:*\n"
            "/start - Авторизация и главное меню\n"
            "/menu - Главное меню\n"
            "/preferences - Настройка интересов\n"
            "/help - Эта справка\n\n"
            "💡 *Совет:* Используйте кнопки меню для удобной навигации!"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("preferences", self.preferences))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("menu", self.menu))
        
        # Callback-обработчики
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        
        # Проверяем авторизацию
        employee, _ = await AuthManager.authorize_employee(user)
        if not employee:
            error_message = await AuthManager.get_unauthorized_message()
            formatted_message = error_message.format(username=user.username or 'ваш_username')
            await update.message.reply_text(formatted_message, parse_mode='Markdown')
            return
        
        # Если пользователь авторизован, предлагаем меню
        await update.message.reply_text(
            "🤖 Используйте команды или меню для навигации:\n"
            "/menu - Главное меню\n"
            "/preferences - Настройки интересов\n" 
            "/help - Помощь",
            parse_mode='Markdown'
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Глобальный обработчик ошибок"""
        logger.error(f"Необработанная ошибка: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла техническая ошибка. Администратор уведомлен."
                )
            except:
                pass  # Игнорируем ошибки при отправке сообщения об ошибке
    
    async def run_async(self):
        """Асинхронный запуск бота с улучшенной обработкой"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN не установлен")
            return
        
        # Создаем приложение с дополнительными настройками
        self.application = (
            Application.builder()
            .token(self.token)
            .read_timeout(30)      # Увеличиваем таймаут чтения
            .write_timeout(30)     # Увеличиваем таймаут записи
            .connect_timeout(20)   # Таймаут подключения
            .pool_timeout(10)      # Таймаут пула соединений
            .get_updates_read_timeout(10)  # Таймаут для getUpdates
            .build()
        )
        
        # Добавляем глобальный обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        self.running = True
        
        try:
            # Инициализируем приложение
            await self.application.initialize()
            await self.application.start()
            
            logger.info("🚀 ConnectBot запущен и готов к работе!")
            
            # Запускаем polling с улучшенными параметрами
            await self.application.updater.start_polling(
                poll_interval=2.0,      # Интервал между запросами
                timeout=10,             # Таймаут long polling
                read_timeout=15,        # Таймаут чтения
                write_timeout=15,       # Таймаут записи
                connect_timeout=10,     # Таймаут подключения
                drop_pending_updates=True  # Сбрасываем старые обновления
            )
            
            # Ждем завершения работы
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
        finally:
            # Корректное завершение
            try:
                if self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Ошибка при завершении: {e}")
            
            logger.info("🛑 ConnectBot остановлен")
    
    def run(self):
        """Запуск бота"""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки от пользователя")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")


def main():
    """Основная функция запуска"""
    print("🚀 Запуск исправленного ConnectBot...")
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем и запускаем бота
    bot = ImprovedConnectBot()
    bot.run()


if __name__ == "__main__":
    main()