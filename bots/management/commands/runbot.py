"""
Django команда для запуска Telegram бота ConnectBot v21
"""
import logging
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск Telegram бота ConnectBot v21'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-scheduler',
            action='store_true',
            help='Запуск с планировщиком задач',
        )

    def handle(self, *args, **options):
        """Основной обработчик команды"""
        # Настройка логирования
        self.setup_logging()
        
        # Проверка токена бота
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('Ошибка: TELEGRAM_BOT_TOKEN не установлен в настройках')
            )
            self.stdout.write('Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env')
            return
        
        self.stdout.write("""
🤖 ConnectBot v21 - Основная команда запуска
📅 Система корпоративных активностей
        """)
        
        if options.get('with_scheduler'):
            self.stdout.write('Режим: С планировщиком задач')
            self._run_with_scheduler()
        else:
            self.stdout.write('Режим: Простой запуск (без планировщика)')
            self._run_simple()

    def _run_simple(self):
        """Простой запуск без планировщика"""
        try:
            from telegram.ext import Application
            from telegram.request import HTTPXRequest
            
            self.stdout.write('Инициализация бота...')
            
            # Создаем простое приложение (сложные настройки вызывали таймауты)
            application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Добавляем базовые обработчики
            self._setup_basic_handlers(application)
            
            self.stdout.write('Бот создан успешно!')
            self.stdout.write('Запуск polling... (Ctrl+C для остановки)')
            
            # Запуск в режиме polling (простые параметры работают лучше)
            application.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
            # Пробуем запустить через simple_bot как fallback
            try:
                self.stdout.write('Попытка запуска через simple_bot...')
                import subprocess
                import sys
                subprocess.run([sys.executable, 'manage.py', 'simple_bot'])
            except Exception as fallback_error:
                self.stdout.write(self.style.ERROR(f'Fallback ошибка: {fallback_error}'))

    def _run_with_scheduler(self):
        """Запуск с планировщиком задач"""
        try:
            from bots.bot_instance import create_bot_application
            from bots.services.scheduler_service import scheduler_service
            
            self.stdout.write('Инициализация бота с планировщиком...')
            
            # Создаем приложение бота
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('Не удалось создать приложение бота'))
                return
            
            # Запускаем планировщик
            scheduler_service.start_scheduler()
            status = scheduler_service.get_scheduler_status()
            self.stdout.write(f"Планировщик: {status['status']}, задач: {status['job_count']}")
            
            self.stdout.write('Запуск polling с планировщиком... (Ctrl+C для остановки)')
            
            # Запуск в режиме polling
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
        finally:
            try:
                scheduler_service.stop_scheduler()
                self.stdout.write('Планировщик остановлен')
            except:
                pass

    def _setup_basic_handlers(self, application):
        """Настройка основных обработчиков"""
        from telegram import Update
        from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
        
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Получена команда /start от пользователя {update.effective_user.id}")
                message = (
                    "👋 Привет! Я ConnectBot v21!\n\n"
                    "🤖 Система корпоративных активностей\n"
                    "📋 Используй /help для справки"
                )
                await update.message.reply_text(message)
                self.stdout.write("Ответ на /start отправлен успешно")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в start_command: {e}"))
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Получена команда /help от пользователя {update.effective_user.id}")
                message = (
                    "🔧 *CONNECTBOT V21 - СПРАВКА*\n\n"
                    "🎯 *Основные команды:*\n"
                    "/start - Запуск и приветствие\n"
                    "/help - Эта справка\n"
                    "/menu - Главное меню\n\n"
                    "☕ *Тайный кофе:*\n"
                    "/coffee - Участие в Тайном кофе\n"
                    "/preferences - Настройки встреч\n\n"
                    "🎯 *Активности:*\n"
                    "/activities - Список активностей\n"
                    "/stats - Моя статистика\n\n"
                    "👤 *Профиль:*\n"
                    "/profile - Мой профиль\n"
                    "/settings - Настройки\n\n"
                    "🧪 *Тест:*\n"
                    "/test - Проверка работы\n\n"
                    "🚀 Бот работает стабильно!"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
                self.stdout.write("Ответ на /help отправлен успешно")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в help_command: {e}"))
        
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Получена команда /test от пользователя {update.effective_user.id}")
                await update.message.reply_text("✅ Тест прошел! Бот работает корректно.")
                self.stdout.write("Ответ на /test отправлен успешно")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в test_command: {e}"))
        
        async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Получено сообщение: '{update.message.text}' от пользователя {update.effective_user.id}")
                await update.message.reply_text(f"Echo: {update.message.text}")
                self.stdout.write("Echo ответ отправлен успешно")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в echo_handler: {e}"))
        
        # Добавляем команды активностей
        async def coffee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /coffee от {update.effective_user.first_name}")
                await update.message.reply_text(
                    "☕ *ТАЙНЫЙ КОФЕ*\n\n"
                    "🤫 Анонимная встреча с коллегой\n"
                    "📋 Используйте /preferences для настройки\n"
                    "🎯 Матчинг каждую неделю по понедельникам\n\n"
                    "💡 Для участия обновите свой профиль!",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /coffee отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в coffee_command: {e}"))
        
        async def activities_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /activities от {update.effective_user.first_name}")
                await update.message.reply_text(
                    "🎯 *КОРПОРАТИВНЫЕ АКТИВНОСТИ*\n\n"
                    "☕ /coffee - Тайный кофе\n"
                    "♟️ Шахматный турнир\n"
                    "🏓 Настольный теннис\n"
                    "📸 Фотоквесты\n"
                    "🧠 Мастер-классы\n\n"
                    "📊 /stats - Моя статистика\n"
                    "⚙️ /settings - Настройки уведомлений",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /activities отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в activities_command: {e}"))
        
        async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /profile от {update.effective_user.first_name}")
                user = update.effective_user
                await update.message.reply_text(
                    f"👤 *МОЙ ПРОФИЛЬ*\n\n"
                    f"🆔 ID: {user.id}\n"
                    f"👋 Имя: {user.first_name}\n"
                    f"📞 Username: @{user.username or 'не указан'}\n\n"
                    f"📊 /stats - Статистика активности\n"
                    f"⚙️ /settings - Настройки профиля\n"
                    f"☕ /preferences - Настройки Тайного кофе",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /profile отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в profile_command: {e}"))
        
        async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /settings от {update.effective_user.first_name}")
                await update.message.reply_text(
                    "⚙️ *НАСТРОЙКИ*\n\n"
                    "🔔 Уведомления: включены\n"
                    "⏰ Время уведомлений: 09:00-18:00\n"
                    "📱 Формат: Telegram\n\n"
                    "☕ /preferences - Настройки Тайного кофе\n"
                    "🔕 /notifications - Управление уведомлениями\n\n"
                    "💡 Скоро будет доступно больше настроек!",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /settings отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в settings_command: {e}"))
        
        async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /stats от {update.effective_user.first_name}")
                await update.message.reply_text(
                    "📊 *МОЯ СТАТИСТИКА*\n\n"
                    "☕ *Тайный кофе:*\n"
                    "   └ Встреч: 0\n"
                    "   └ Рейтинг: новичок\n\n"
                    "🎯 *Активности:*\n"
                    "   └ Участий: 0\n"
                    "   └ Очков: 0\n\n"
                    "📈 *Общее:*\n"
                    "   └ Дней в системе: 1\n"
                    "   └ Активность: начинающий\n\n"
                    "💡 Участвуйте в активностях для роста статистики!",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /stats отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в stats_command: {e}"))
        
        async def preferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                self.stdout.write(f"Команда /preferences от {update.effective_user.first_name}")
                await update.message.reply_text(
                    "☕ *НАСТРОЙКИ ТАЙНОГО КОФЕ*\n\n"
                    "🕐 Доступность: не настроено\n"
                    "💻 Формат встреч: не указан\n"
                    "🎯 Темы интересов: не выбраны\n\n"
                    "⚙️ Используйте кнопки ниже для настройки:\n"
                    "• Укажите удобное время\n"
                    "• Выберите формат (онлайн/оффлайн)\n"
                    "• Отметьте интересные темы\n\n"
                    "💡 Настройки помогут найти подходящего собеседника!",
                    parse_mode='Markdown'
                )
                self.stdout.write("✅ Ответ на /preferences отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в preferences_command: {e}"))

        # Регистрируем все обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("menu", help_command))  # menu = help для простоты
        application.add_handler(CommandHandler("coffee", coffee_command))
        application.add_handler(CommandHandler("activities", activities_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("preferences", preferences_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
        
        self.stdout.write("✅ Все обработчики команд зарегистрированы:")

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )