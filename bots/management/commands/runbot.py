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
🔔 С системой умных уведомлений в меню
        """)
        
        if options.get('with_scheduler'):
            self.stdout.write('Режим: С планировщиком задач')
            self._run_with_scheduler()
        else:
            self.stdout.write('Режим: Простой запуск (без планировщика)')
            self._run_simple()

    def _run_simple(self):
        """Простой запуск без планировщика"""
        # Обёртка: держим процесс живым и повторяем попытки при временных сетевых ошибках
        from telegram.ext import Application
        from telegram.request import HTTPXRequest
        import httpx
        import time
        from bots.utils.retry_utils import sync_retry_decorator
        from httpx import ConnectError, ReadTimeout, HTTPError

        attempts_outer = 0
        while True:
            try:
                attempts_outer += 1
                self.stdout.write('Инициализация бота с системой уведомлений...')

                # Создаем HTTPX клиент с увеличенными таймаутами
                transport = None
                try:
                    if hasattr(httpx, 'AsyncHTTPTransport'):
                        try:
                            transport = httpx.AsyncHTTPTransport(retries=5)
                            self.stdout.write('Using AsyncHTTPTransport(retries=5)')
                        except TypeError:
                            transport = httpx.AsyncHTTPTransport()
                            self.stdout.write('Using AsyncHTTPTransport() without retries')

                    if transport:
                        httpx_client = httpx.AsyncClient(
                            transport=transport,
                            timeout=httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=60.0),
                            limits=httpx.Limits(max_connections=60, max_keepalive_connections=20),
                            trust_env=False,
                        )
                    else:
                        httpx_client = httpx.AsyncClient(
                            timeout=httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=60.0),
                            limits=httpx.Limits(max_connections=60, max_keepalive_connections=20),
                            trust_env=False,
                        )
                except Exception:
                    httpx_client = httpx.AsyncClient(
                        timeout=httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=60.0),
                        limits=httpx.Limits(max_connections=60, max_keepalive_connections=20),
                        trust_env=False,
                    )

                try:
                    request = HTTPXRequest(client=httpx_client)
                    self.stdout.write('Using HTTPXRequest(client=AsyncClient)')
                except TypeError:
                    try:
                        request = HTTPXRequest(http_version="1.1", client=httpx_client)
                        self.stdout.write('Using HTTPXRequest(http_version, client=AsyncClient)')
                    except TypeError:
                        request = HTTPXRequest()
                        self.stdout.write('Using default HTTPXRequest() fallback')

                application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).request(request).build()

                # Добавляем базовые обработчики
                self._setup_basic_handlers(application)

                self.stdout.write('✅ Бот создан успешно!')
                self.stdout.write('🔔 Система уведомлений активирована')
                self.stdout.write('📱 ReplyKeyboard с счетчиками готов к работе')
                self.stdout.write('Запуск polling... (Ctrl+C для остановки)')

                # Запуск в режиме polling — внутренняя повторная попытка на уровне run_polling
                # Ретрай на уровне run_polling — не передаём устаревший get_updates_request,
                # т.к. разные версии PTB принимают разные параметры.
                from telegram.error import Conflict as TelegramConflict

                @sync_retry_decorator(attempts=8, min_wait=2, max_wait=60, retry_exceptions=(ConnectError, ReadTimeout, HTTPError, TelegramConflict))
                def _run_polling_with_retry():
                    try:
                        # Универсальный вызов: пусть библиотека сама использует подходящий метод.
                        application.run_polling(drop_pending_updates=True)
                    except KeyboardInterrupt:
                        raise

                _run_polling_with_retry()

                # Если run_polling завершился без исключений, выходим из цикла
                break

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
                break
            except Exception as e:
                # Логируем и ждём перед следующей попыткой, не завершая процесс
                self.stdout.write(self.style.ERROR(f'Ошибка при запуске бота (попытка {attempts_outer}): {e}'))
                wait_seconds = min(60, 2 ** min(attempts_outer, 6))
                self.stdout.write(f'Повторная попытка через {wait_seconds} секунд...')
                try:
                    time.sleep(wait_seconds)
                except KeyboardInterrupt:
                    break

    def _run_with_scheduler(self):
        """Запуск с планировщиком задач"""
        try:
            from bots.bot_instance import create_bot_application
            from bots.services.scheduler_service import scheduler_service
            
            self.stdout.write('Инициализация бота с планировщиком...')
            
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('Не удалось создать приложение бота'))
                return
            
            scheduler_service.start_scheduler()
            status = scheduler_service.get_scheduler_status()
            self.stdout.write(f"Планировщик: {status['status']}, задач: {status['job_count']}")
            
            self.stdout.write('Запуск polling с планировщиком... (Ctrl+C для остановки)')
            
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
        """Настройка основных обработчиков с поддержкой уведомлений"""
        from telegram import Update
        from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
        
        # Импортируем обработчики старта с уведомлениями
        from bots.handlers.start_handlers import start_command, help_command, menu_command, handle_text_messages, notifications_command, refresh_command
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("notifications", notifications_command))
        application.add_handler(CommandHandler("refresh", refresh_command))
        
        # Регистрируем обработчик текстовых сообщений для навигации
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
        
        # Базовые команды для обратной совместимости с уведомлениями
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Получена команда /test от пользователя {user_id}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                
                # Показываем тестовое сообщение с уведомлениями
                counts = await MenuManager.get_notification_counts(user_id)
                
                test_text = f"""
✅ Тест прошел! Бот работает корректно.

🔔 *Текущие уведомления:*
• Ожидающие встречи: {counts['meetings']}
• Активности сегодня: {counts['today_activities']}
• Всего действий: {counts['total']}

💡 Система уведомлений активна!
"""
                await reply_with_menu(update, test_text, menu_type='main', parse_mode='Markdown', user_id=user_id)
                self.stdout.write("✅ Ответ на /test отправлен с уведомлениями")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в test_command: {e}"))
        
        async def coffee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /coffee от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                coffee_text = await MenuManager.create_coffee_menu()
                await reply_with_menu(update, coffee_text, menu_type='coffee', parse_mode='Markdown', user_id=user_id)
                self.stdout.write("✅ Ответ на /coffee отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в coffee_command: {e}"))
        
        async def activities_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /activities от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                
                counts = await MenuManager.get_notification_counts(user_id)
                
                await reply_with_menu(update,
                    f"""🎯 *КОРПОРАТИВНЫЕ АКТИВНОСТИ*

🔔 *Текущая активность:*
• Ожидающие подтверждения: {counts['today_activities']}
• Активностей на неделе: {counts['week_activities']}

Используйте кнопки в главном меню для выбора активностей:

• ☕ Тайный кофе
• 🎯 Мои интересы  
• 📅 Календарь

💡 Все активности теперь доступны через удобное меню с уведомлениями!""",
                    menu_type='main',
                    parse_mode='Markdown',
                    user_id=user_id
                )
                self.stdout.write("✅ Ответ на /activities отправлен с уведомлениями")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в activities_command: {e}"))
        
        async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /profile от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                from employees.models import Employee
                
                user = update.effective_user
                employee = await Employee.objects.aget(telegram_id=user.id)
                profile_text = await MenuManager.create_profile_menu(employee)
                await reply_with_menu(update, profile_text, menu_type='profile', parse_mode='Markdown', user_id=user_id)
                self.stdout.write("✅ Ответ на /profile отправлен с уведомлениями")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в profile_command: {e}"))
        
        async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /settings от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                settings_text = await MenuManager.create_settings_menu()
                await reply_with_menu(update, settings_text, menu_type='settings', parse_mode='Markdown', user_id=user_id)
                self.stdout.write("✅ Ответ на /settings отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в settings_command: {e}"))
        
        async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /stats от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                
                counts = await MenuManager.get_notification_counts(user_id)
                
                await reply_with_menu(update,
                    f"""📊 *МОЯ СТАТИСТИКА*

🔔 *Текущие показатели:*
• Ожидающие действия: {counts['total']}
• Активности сегодня: {counts['today_activities']}
• Встреч в процессе: {counts['meetings']}

Для просмотра статистики используйте:

• 👤 Мой профиль - основная статистика
• 📊 Статистика - детальная информация  
• 🏆 Мои достижения - ваши награды

💡 Все данные теперь доступны через удобное меню с уведомлениями!""",
                    menu_type='main',
                    parse_mode='Markdown',
                    user_id=user_id
                )
                self.stdout.write("✅ Ответ на /stats отправлен с уведомлениями")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в stats_command: {e}"))
        
        async def preferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                self.stdout.write(f"Команда /preferences от {update.effective_user.first_name}")
                from bots.utils.message_utils import reply_with_menu
                from bots.menu_manager import MenuManager
                from employees.models import Employee
                
                user = update.effective_user
                employee = await Employee.objects.aget(telegram_id=user.id)
                interests_text = await MenuManager.create_interests_menu(employee)
                await reply_with_menu(update, interests_text, menu_type='interests', parse_mode='Markdown', user_id=user_id)
                self.stdout.write("✅ Ответ на /preferences отправлен")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в preferences_command: {e}"))

        # Регистрируем дополнительные команды для обратной совместимости
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("coffee", coffee_command))
        application.add_handler(CommandHandler("activities", activities_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("preferences", preferences_command))

        # Регистрируем дополнительные обработчики для уведомлений
        try:
            # Menu handlers для обратной совместимости
            from bots.handlers.menu_handlers import setup_menu_handlers
            setup_menu_handlers(application)
            self.stdout.write("Registered menu callback handlers")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not register menu handlers: {e}"))

        try:
            # Secret coffee handlers
            from bots.handlers.secret_coffee_handlers import setup_secret_coffee_handlers
            setup_secret_coffee_handlers(application)
            self.stdout.write("Registered secret coffee callback handlers")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not register secret coffee handlers: {e}"))

        try:
            # Preference handlers
            from bots.handlers.preference_handlers import setup_preference_handlers
            setup_preference_handlers(application)
            self.stdout.write("Registered preference callback handlers")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not register preference handlers: {e}"))

        try:
            # Feedback conversation handler
            from bots.handlers.feedback_handlers import feedback_conv_handler
            application.add_handler(feedback_conv_handler)
            self.stdout.write("Registered feedback conversation handler")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not register feedback handler: {e}"))

        self.stdout.write("✅ Все обработчики команд зарегистрированы")
        self.stdout.write("📱 Используется ReplyKeyboardMarkup с системой уведомлений")
        self.stdout.write("🔔 Счетчики уведомлений активны на всех кнопках меню")

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )