"""
Django команда для запуска Telegram бота ConnectBot v21
"""
import logging
import sys
import os
import signal
import asyncio
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
ConnectBot v21 - Основная команда запуска
Система корпоративных активностей
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
            from bots.bot_instance import create_bot_application
            from bots.utils.message_utils import reply_with_footer
            
            self.stdout.write('Инициализация бота...')
            
            # Создаем приложение бота
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('Не удалось создать приложение бота'))
                return
            
            self.stdout.write('Бот создан успешно!')
            self.stdout.write('Запуск polling... (Ctrl+C для остановки)')
            
            # Запуск в режиме polling
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))

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

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )


    # --- Старые асинхронные методы сохранены в архиве для восстановления ---

    # Этот файл является резервной копией старой реализации и перемещён в архив
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
ConnectBot v21 - Основная команда запуска
Система корпоративных активностей
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
            from bots.bot_instance import create_bot_application
            from bots.utils.message_utils import reply_with_footer
            
            self.stdout.write('Инициализация бота...')
            
            # Создаем приложение бота
            application = create_bot_application()
            if not application:
                self.stdout.write(self.style.ERROR('Не удалось создать приложение бота'))
                return
            
            self.stdout.write('Бот создан успешно!')
            self.stdout.write('Запуск polling... (Ctrl+C для остановки)')
            
            # Запуск в режиме polling
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nОстановка по команде пользователя'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))

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

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.scheduler = None
    
    async def initialize(self):
        """Инициализация бота и планировщика"""
        try:
            # Импорты внутри функции чтобы избежать циклических импортов
            from bots.bot_instance import create_bot_application
            from bots.services.scheduler_service import scheduler_service
            
            logger.info("🚀 Инициализация ConnectBot v21...")
            
            # Создаем приложение бота
            self.application = create_bot_application()
            if not self.application:
                logger.error("❌ Не удалось создать приложение бота")
                return False
            
            # Инициализируем планировщик
            self.scheduler = scheduler_service
            
            # Регистрируем админ-команды
            await self.setup_admin_handlers()
            
            logger.info("✅ Бот и планировщик инициализированы")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False

    async def setup_admin_handlers(self):
        """Настройка обработчиков админ-команд"""
        try:
            from telegram.ext import CommandHandler
            
            # Добавляем админ-команды в приложение
            self.application.add_handler(CommandHandler("admin", self.handle_admin_command))
            self.application.add_handler(CommandHandler("admin_dashboard", self.handle_admin_dashboard))
            self.application.add_handler(CommandHandler("admin_stats", self.handle_admin_stats))
            self.application.add_handler(CommandHandler("admin_health", self.handle_admin_health))
            self.application.add_handler(CommandHandler("admin_activities", self.handle_admin_activities))
            self.application.add_handler(CommandHandler("admin_meetings", self.handle_admin_meetings))
            self.application.add_handler(CommandHandler("admin_users", self.handle_admin_users))
            
            logger.info("✅ Админ-команды зарегистрированы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки админ-обработчиков: {e}")

    async def handle_admin_command(self, update, context):
        """Обработчик команды /admin"""
        telegram_id = update.effective_user.id
        
        # Проверка прав администратора
        if not await AdminAuthService.is_user_admin(telegram_id):
            await reply_with_footer(update,
                "❌ У вас нет прав доступа к админ-панели.\n"
                "Обратитесь к системному администратору."
            )
            return
        
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin')
        
        help_text = """
🔧 **ПАНЕЛЬ АДМИНИСТРАТОРА**

Основные команды:
📊 /admin_dashboard - Общая статистика
📈 /admin_stats - Детальная статистика
❤️ /admin_health - Состояние системы
🎯 /admin_activities - Управление активностями
🤝 /admin_meetings - Управление встречами
👥 /admin_users - Управление пользователями

Для помощи по конкретной команде используйте /admin_help [команда]
        """
        
        await reply_with_footer(update, help_text, parse_mode='Markdown')
    
    async def handle_admin_dashboard(self, update, context):
        """Панель управления администратора"""
        telegram_id = update.effective_user.id
        
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin_dashboard')
        
        # Получаем статистику
        system_stats = await AdminStatsService.get_system_stats()
        
        dashboard_text = f"""
📊 **ПАНЕЛЬ УПРАВЛЕНИЯ CONNECTBOT**

👥 **Пользователи:** {system_stats['total_users']}
🤝 **Активные встречи:** {system_stats['active_meetings']}
☕ **Кофе-сессии:** {system_stats['coffee_sessions']}
📈 **Успешность matching:** {system_stats['matching_rate']}%

⚙️ **Команды управления:**
/admin_stats - Детальная статистика
/admin_health - Состояние системы
/admin_activities - Активности
/admin_meetings - Встречи
        """
        
        await reply_with_footer(update, dashboard_text, parse_mode='Markdown')

    async def handle_admin_stats(self, update, context):
        """Детальная статистика"""
        telegram_id = update.effective_user.id
        
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin_stats')
        
        system_stats = await AdminStatsService.get_system_stats()
        
        stats_text = f"""
📈 **ДЕТАЛЬНАЯ СТАТИСТИКА**

👥 **Пользователи:**
   • Всего сотрудников: {system_stats['total_users']}

🤝 **Встречи:**
   • Активные встречи: {system_stats['active_meetings']}
   • Всего кофе-сессий: {system_stats['coffee_sessions']}
   • Успешность matching: {system_stats['matching_rate']}%

🔄 **Последнее обновление:** {timezone.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        await reply_with_footer(update, stats_text, parse_mode='Markdown')

    async def handle_admin_health(self, update, context):
        """Состояние системы"""
        telegram_id = update.effective_user.id
        
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        await reply_with_footer(update, help_text, parse_mode='Markdown')
        await AdminLogService.log_action(admin_user, 'command', '/admin_health')
        
        health_status = await SystemHealthService.check_system_health()
        
        status_emoji = "❤️" if health_status['status'] == 'healthy' else "💔"
        status_text = "ЗДОРОВА" if health_status['status'] == 'healthy' else "НЕИСПРАВНА"
        
        health_text = f"""
{status_emoji} **СОСТОЯНИЕ СИСТЕМЫ: {status_text}**

**Компоненты:**
"""
        
        for component, info in health_status['components'].items():
            emoji = "✅" if info['status'] == 'healthy' else "❌"
            component_name = {
                'database': 'База данных',
                'redis': 'Redis кэш'
            }.get(component, component)
            
            health_text += f"{emoji} {component_name}: {info['details']}\n"
        
        health_text += f"\n🕐 Проверено: {health_status['timestamp'][11:16]}"
        
        await reply_with_footer(update, health_text, parse_mode='Markdown')

    async def handle_admin_activities(self, update, context):
        """Управление активностями"""
        telegram_id = update.effective_user.id
        await reply_with_footer(update, dashboard_text, parse_mode='Markdown')
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin_activities')
        
        activities_text = """
🎯 **УПРАВЛЕНИЕ АКТИВНОСТЯМИ**

Доступные команды:
• /admin_activities_list - Список активностей
• /admin_activities_create - Создать активность
• /admin_activities_pause - Приостановить активность

📊 Используйте /admin_stats для просмотра статистики по активностям.
        """
        
        await reply_with_footer(update, activities_text, parse_mode='Markdown')

    async def handle_admin_meetings(self, update, context):
        """Управление встречами"""
        telegram_id = update.effective_user.id
        
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        await reply_with_footer(update, stats_text, parse_mode='Markdown')
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin_meetings')
        
        meetings_text = """
🤝 **УПРАВЛЕНИЕ ВСТРЕЧАМИ**

Доступные команды:
• /admin_meetings_active - Активные встречи
• /admin_meetings_history - История встреч
• /admin_meetings_cancel - Отменить встречу

⚠️ Для экстренной остановки встречи используйте /admin_emergency_stop
        """
        
        await reply_with_footer(update, meetings_text, parse_mode='Markdown')

    async def handle_admin_users(self, update, context):
        """Управление пользователями"""
        telegram_id = update.effective_user.id
        
        if not await AdminAuthService.is_user_admin(telegram_id):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        admin_user = await AdminAuthService.get_admin_user(telegram_id)
        await AdminLogService.log_action(admin_user, 'command', '/admin_users')
        
        users_text = """
👥 **УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ**

Доступные команды:
• /admin_users_list - Список пользователей
• /admin_users_manage - Управление пользователем
        """
        
        await reply_with_footer(update, users_text, parse_mode='Markdown')
    
    async def start_services(self):
        """Запуск всех сервисов бота"""
        try:
            logger.info("📦 Запуск сервисов ConnectBot...")
            
            # Запускаем планировщик задач
            self.scheduler.start_scheduler()
            
            # Проверяем статус планировщика
            status = self.scheduler.get_scheduler_status()
            logger.info(f"📅 Планировщик: {status['status']}, задач: {status['job_count']}")
            
            # Показываем информацию о задачах
            for job in status['jobs']:
                logger.info(f"   🎯 {job['name']} -> {job['next_run']}")
            
            await self.scheduler._create_weekly_sessions_async()
            
            logger.info("✅ Все сервисы успешно запущены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска сервисов: {e}")
            return False

    async def stop_services(self):
        """Остановка всех сервисов бота"""
        try:
            logger.info("🛑 Остановка сервисов ConnectBot...")
            
            if self.scheduler:
                self.scheduler.stop_scheduler()
                logger.info("✅ Планировщик остановлен")
            
            logger.info("✅ Все сервисы остановлены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки сервисов: {e}")
        await reply_with_footer(update, meetings_text, parse_mode='Markdown')

    async def run_bot(self):
        """Запуск polling бота"""
        try:
            if not self.application:
                logger.error("❌ Приложение бота не инициализировано")
                return
            
            logger.info("🤖 Запуск Telegram бота (polling)...")
            await self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка работы бота: {e}")
            raise

    async def run(self):
        """Основной метод запуска бота"""
        try:
            # Инициализация
            if not await self.initialize():
                return
            
            # Запуск сервисов
            if not await self.start_services():
                return
            
            # Запуск бота
            await self.run_bot()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по команде пользователя...")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка: {e}")
        finally:
            # Гарантированная остановка сервисов
            await self.stop_services()
            logger.info("👋 ConnectBot завершил работу")

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    print(f"\n🛑 Получен сигнал {signum}. Остановка ConnectBot...")
    
    # Останавливаем event loop
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
    
    sys.exit(0)

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/bot.log', encoding='utf-8')
        ]
    )

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создание и запуск бота
    bot = ConnectBot()
    
    try:
        # Запуск асинхронного бота
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по команде пользователя")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверка токена бота
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен в настройках")
        print("💡 Добавьте TELEGRAM_BOT_TOKEN=ваш_токен в файл .env")
        sys.exit(1)
    
    # Проверка существования папки logs
    os.makedirs('logs', exist_ok=True)
    
    print("""
    🚀 ConnectBot v21
    📅 Система корпоративных активностей
    🤖 Тайный кофе • Шахматы • Мероприятия
    🔧 Версия с планировщиком задач
    👑 Админ-панель включена
    """)
    
    main()
# Legacy backup of runbot - preserved for archive
# (original content removed for brevity; archived full version retained by developer request)

# NOTE: This file contained multiple deprecated and broken constructs and was removed from main tree.
# Full original content is preserved here for reference.