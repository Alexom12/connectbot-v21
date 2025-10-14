"""
Основной модуль Telegram бота ConnectBot
Версия с исправлениями конфликтов getUpdates
"""
import asyncio
import logging
import signal
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from asgiref.sync import sync_to_async

from employees.utils import AuthManager, PreferenceManager
from employees.redis_utils import RedisManager
from bots.menu_manager import MenuManager

logger = logging.getLogger(__name__)


class ConnectBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()
        self.running = False
        
        # Добавляем обработку сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if self.redis_available:
            logger.info("Redis доступен, включено кеширование сессий")
        else:
            logger.warning("Redis недоступен, кеширование сессий отключено")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, останавливаем бот...")
        self.running = False
        # Используем более мягкий способ остановки
        if hasattr(self, 'application') and self.application:
            try:
                self.application.stop_running()
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")
    
    async def shutdown(self):
        """Корректное завершение работы бота"""
        try:
            logger.info("Начинаем корректное завершение...")
            if hasattr(self, 'application') and self.application:
                # Останавливаем polling и приложение
                if self.application.running:
                    await self.application.stop()
                if not self.application._initialized:
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
                "Произошла ошибка при авторизации. Попробуйте позже или обратитесь к администратору."
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
    
    async def show_calendar_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee):
        """Показать меню календаря"""
        menu_data = await MenuManager.create_calendar_menu(employee)
        await update.callback_query.edit_message_text(**menu_data)
    
    async def show_achievements_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, employee):
        """Показать меню достижений"""
        menu_data = await MenuManager.create_achievements_menu(employee)
        await update.callback_query.edit_message_text(**menu_data)
    
    async def show_help_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню помощи"""
        menu_data = await MenuManager.create_help_menu()
        await update.callback_query.edit_message_text(**menu_data)
    
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню настроек"""
        menu_data = await MenuManager.create_settings_menu()
        await update.callback_query.edit_message_text(**menu_data)
    
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
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    
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
                    "Ваша сессия устарела. Используйте /start для повторной авторизации."
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
                
            elif callback_data == "menu_calendar":
                await self.show_calendar_menu(update, context, employee)
                
            elif callback_data == "menu_achievements":
                await self.show_achievements_menu(update, context, employee)
                
            elif callback_data == "menu_help":
                await self.show_help_menu(update, context)
                
            elif callback_data == "menu_settings":
                await self.show_settings_menu(update, context)
                
            # Обработка кнопки Назад
            elif callback_data.startswith("back_"):
                target = callback_data.replace("back_", "")
                if target == "main":
                    await self.show_main_menu(update, context)
                elif target == "profile":
                    await self.show_profile_menu(update, context, employee)
                # Можно добавить другие цели для назад
                
            # Настройка предпочтений
            elif callback_data == "setup_preferences":
                await self.show_interests_menu(update, context, employee)
                
            elif callback_data == "skip_setup":
                await query.edit_message_text(
                    "Отлично! Вы можете настроить интересы позже через команду /preferences\n\n"
                    "Переходим в главное меню...",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(2)
                await self.show_main_menu(update, context)
                
            # Управление интересами
            elif callback_data.startswith("toggle_interest_"):
                await self.handle_interest_toggle(query, context, employee, callback_data)
                
            elif callback_data == "save_interests":
                await self.save_interests(query, context, employee)
                
            elif callback_data == "disable_all_interests":
                await self.show_disable_all_confirmation(query, context)
                
            elif callback_data == "confirm_disable_all":
                await self.disable_all_interests(query, context, employee)
                
            elif callback_data == "cancel_disable_all":
                await self.show_interests_menu(update, context, employee)
                
            # Помощь
            elif callback_data.startswith("help_"):
                await self.show_help_topic(query, context, callback_data)
                
            else:
                await query.edit_message_text(
                    "Функция в разработке...\n\n"
                    "Скоро здесь появится новый функционал!",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            try:
                await query.edit_message_text("Произошла ошибка. Попробуйте позже.")
            except:
                # Если не удалось отредактировать сообщение, попробуем ответить
                try:
                    await query.answer("Произошла ошибка", show_alert=True)
                except:
                    pass  # Игнорируем ошибки при уведомлении
    
    async def handle_interest_toggle(self, query, context, employee, callback_data):
        """Обработка переключения интереса"""
        interest_code = callback_data.replace("toggle_interest_", "")
        user = query.from_user
        
        # Получаем все интересы
        all_interests = await PreferenceManager.get_all_interests()
        employee_interests = await PreferenceManager.get_employee_interests(employee)
        
        # Находим текущий интерес
        current_interest = next((i for i in all_interests if i.code == interest_code), None)
        if not current_interest:
            await query.answer("Интерес не найден", show_alert=True)
            return
        
        # Определяем текущий статус
        current_ei = next((ei for ei in employee_interests if ei.interest.code == interest_code), None)
        is_currently_active = current_ei.is_active if current_ei else False
        new_status = not is_currently_active
        
        status_text = "ВКЛ" if new_status else "ВЫКЛ"
        
        await query.answer(
            f"Будет установлено: {status_text} {current_interest.name}\n"
            f"Не забудьте сохранить изменения!",
            show_alert=False
        )
        
        # Сохраняем в Redis сессии и контексте временное состояние
        session_data = await self.get_user_session(user.id)
        if 'pending_interests' not in session_data:
            session_data['pending_interests'] = {}
        session_data['pending_interests'][interest_code] = new_status
        
        await self.update_user_session(user.id, {'pending_interests': session_data['pending_interests']})
        
        # Дублируем в контекст для совместимости
        if 'pending_interests' not in context.user_data:
            context.user_data['pending_interests'] = {}
        context.user_data['pending_interests'][interest_code] = new_status
    
    async def save_interests(self, query, context, employee):
        """Сохранение изменений интересов"""
        try:
            user = query.from_user
            
            # Получаем pending_interests из Redis сессии или контекста
            session_data = await self.get_user_session(user.id)
            pending_interests = session_data.get('pending_interests', {})
            
            if not pending_interests:
                pending_interests = context.user_data.get('pending_interests', {})
            
            if not pending_interests:
                await query.answer("Нет изменений для сохранения", show_alert=True)
                return
            
            # Применяем изменения
            success = await PreferenceManager.update_employee_interests(
                employee, 
                [code for code, active in pending_interests.items() if active]
            )
            
            if success:
                # Очищаем временные данные из обеих систем
                context.user_data['pending_interests'] = {}
                await self.update_user_session(user.id, {'pending_interests': {}})
                
                # Инвалидируем кеш интересов сотрудника
                await RedisManager.async_invalidate_employee_cache(employee.id)
                
                await query.answer("Изменения сохранены!", show_alert=True)
                # Обновляем меню - создаем Update из query
                fake_update = type('Update', (), {'callback_query': query})()
                await self.show_interests_menu(fake_update, context, employee)
            else:
                await query.answer("Ошибка сохранения", show_alert=True)
                
        except Exception as e:
            logger.error(f"Ошибка сохранения интересов: {e}")
            await query.answer("Ошибка сохранения", show_alert=True)
    
    async def show_disable_all_confirmation(self, query, context):
        """Подтверждение отписки от всех интересов"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("Да, отписаться", callback_data="confirm_disable_all")],
            [InlineKeyboardButton("Отмена", callback_data="cancel_disable_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "*Отписка от всех активностей*\n\n"
            "Вы уверены, что хотите отписаться от всех уведомлений?\n\n"
            "После этого вы не будете получать приглашения на мероприятия.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def disable_all_interests(self, query, context, employee):
        """Отписка от всех интересов"""
        try:
            user = query.from_user
            success = await PreferenceManager.disable_all_interests(employee)
            
            if success:
                # Очищаем временные данные из обеих систем
                context.user_data['pending_interests'] = {}
                await self.update_user_session(user.id, {'pending_interests': {}})
                
                # Инвалидируем кеш интересов сотрудника
                await RedisManager.async_invalidate_employee_cache(employee.id)
                
                await query.answer("Отписались от всех активностей!", show_alert=True)
                # Создаем Update из query для обновления меню
                fake_update = type('Update', (), {'callback_query': query})()
                await self.show_interests_menu(fake_update, context, employee)
            else:
                await query.answer("Ошибка отписки", show_alert=True)
                
        except Exception as e:
            logger.error(f"Ошибка отписки от всех интересов: {e}")
            await query.answer("Ошибка отписки", show_alert=True)
    
    async def show_help_topic(self, query, context, callback_data):
        """Показать конкретную тему помощи"""
        topic = callback_data.replace("help_", "")
        
        help_topics = {
            'interests': """
❓ *Как изменить интересы?*

1. Откройте Главное меню → 🎯 Мои интересы
2. Нажмите на интерес для переключения (✅/❌)
3. Сохраните изменения кнопкой «💾 Сохранить»

Изменения вступают в силу сразу!
""",
            'optout': """
❓ *Как отказаться от активности?*

• В приглашении: нажмите «Пропущу» или «Не участвую»
• В настройках: снимите галочки с ненужных активностей  
• Полный отказ: кнопка «Отписаться от всего»

Можно вернуться в любой момент!
""",
            'notifications': """
❓ *Не приходят уведомления?*

1. Проверьте настройки интересов (/preferences)
2. Убедитесь, что подписаны на нужные активности
3. Проверьте, не отключили ли уведомления в Telegram
4. Обратитесь к администратору если проблема persists
""",
            'contact_admin': """
📞 *Связь с администратором*

По вопросам работы бота обращайтесь:

• Telegram: @hr_admin
• Email: hr@company.com
• Внутренний чат: #connectbot-support

Мы поможем решить любые проблемы! 🤝
"""
        }
        
        if topic in help_topics:
            reply_markup = await MenuManager.create_back_button("help")
            await query.edit_message_text(
                help_topics[topic],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.answer("Тема помощи не найдена", show_alert=True)
    
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
        
        # Добавляем глобальный обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
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
        # Игнорируем ошибки HTTPXRequest во время завершения
        error_str = str(context.error)
        if ("HTTPXRequest" in error_str or 
            "httpx" in error_str.lower() or 
            not self.running):
            return
            
        logger.error(f"Необработанная ошибка: {context.error}")
        
        if update and update.effective_message and self.running:
            try:
                await update.effective_message.reply_text(
                    "Произошла техническая ошибка. Администратор уведомлен."
                )
            except:
                pass  # Игнорируем ошибки при отправке сообщения об ошибке
    

    
    def run(self):
        """Запуск бота - синхронный"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN не установлен")
            return
            
        try:
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
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            logger.info("ConnectBot запущен и готов к работе!")
            
            # Запускаем polling - это блокирующий вызов
            try:
                self.application.run_polling(
                    poll_interval=2.0,      # Интервал между запросами
                    timeout=10,             # Таймаут long polling
                    drop_pending_updates=True,  # Сбрасываем старые обновления
                    close_loop=False       # Не закрываем event loop принудительно
                )
            except KeyboardInterrupt:
                logger.info("Получение Ctrl+C, корректно завершаем...")
                self.running = False
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки от пользователя")
        except Exception as e:
            if self.running:  # Логируем только если бот еще работает
                logger.error(f"Критическая ошибка: {e}")
        finally:
            logger.info("ConnectBot остановлен")


class Command(BaseCommand):
    """Django management команда для запуска Telegram бота"""
    
    help = 'Запуск Telegram бота ConnectBot'
    
    def handle(self, *args, **options):
        """Обработчик команды"""
        self.stdout.write(self.style.SUCCESS('Запуск ConnectBot...'))
        
        bot = ConnectBot()
        bot.run()