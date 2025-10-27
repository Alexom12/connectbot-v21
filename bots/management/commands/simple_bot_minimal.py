"""
Упрощенная команда запуска бота без сложных настроек
Для решения проблем с таймаутами
"""
import logging
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from bots.utils.message_utils import reply_with_footer

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Упрощенный запуск Telegram бота'

    def handle(self, *args, **options):
        """Основной обработчик команды"""
        
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(self.style.ERROR('TELEGRAM_BOT_TOKEN не установлен'))
            return
        
        self.stdout.write("🤖 ConnectBot v21 - Упрощенный запуск")
        self._run_simple_bot()

    def _run_simple_bot(self):
        """Запуск максимально простого бота"""
        try:
            from telegram.ext import Application, CommandHandler
            
            self.stdout.write('Создание бота...')
            
            # Максимально простое приложение
            app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            
            # Полный набор обработчиков команд
            async def start(update, context):
                self.stdout.write(f"Команда /start от {update.effective_user.first_name}")
                try:
                    user = update.effective_user
                    message = f"""👋 Привет, {user.first_name}!

🤖 Я ConnectBot v21 - твой помощник для корпоративных активностей!

📋 Мои возможности:
☕ Тайный кофе - найди коллегу для кофе-брейка
🎯 Активности - участвуй в корпоративных мероприятиях
📊 Статистика - отслеживай свою активность
⚙️ Настройки - управляй уведомлениями

Используй /help для полного списка команд."""
                    await reply_with_footer(update, message)
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")
            
            async def help_cmd(update, context):
                self.stdout.write(f"Команда /help от {update.effective_user.first_name}")
                try:
                    message = """🔧 *CONNECTBOT V21 - СПРАВКА*

🎯 *Основные команды:*
/start - Запуск и приветствие
/help - Эта справка
/menu - Главное меню

☕ *Тайный кофе:*
/coffee - Участие в Тайном кофе
/preferences - Настройки встреч

🎯 *Активности:*
/activities - Список активностей
/stats - Моя статистика

👤 *Профиль:*
/profile - Мой профиль
/settings - Настройки

🧪 *Тест:*
/test - Проверка работы

🚀 Бот работает стабильно!"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def coffee_cmd(update, context):
                self.stdout.write(f"Команда /coffee от {update.effective_user.first_name}")
                try:
                    message = """☕ *ТАЙНЫЙ КОФЕ*

🤫 Анонимная встреча с коллегой
📋 Используйте /preferences для настройки
🎯 Матчинг каждую неделю по понедельникам

💡 Для участия обновите свой профиль!"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def activities_cmd(update, context):
                self.stdout.write(f"Команда /activities от {update.effective_user.first_name}")
                try:
                    message = """🎯 *КОРПОРАТИВНЫЕ АКТИВНОСТИ*

☕ /coffee - Тайный кофе
♟️ Шахматный турнир
🏓 Настольный теннис
📸 Фотоквесты
🧠 Мастер-классы

📊 /stats - Моя статистика
⚙️ /settings - Настройки уведомлений"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def profile_cmd(update, context):
                self.stdout.write(f"Команда /profile от {update.effective_user.first_name}")
                try:
                    user = update.effective_user
                    message = f"""👤 *МОЙ ПРОФИЛЬ*

🆔 ID: {user.id}
👋 Имя: {user.first_name}
📞 Username: @{user.username or 'не указан'}

📊 /stats - Статистика активности
⚙️ /settings - Настройки профиля
☕ /preferences - Настройки Тайного кофе"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def settings_cmd(update, context):
                self.stdout.write(f"Команда /settings от {update.effective_user.first_name}")
                try:
                    message = """⚙️ *НАСТРОЙКИ*

🔔 Уведомления: включены
⏰ Время уведомлений: 09:00-18:00
📱 Формат: Telegram

☕ /preferences - Настройки Тайного кофе
🔕 /notifications - Управление уведомлениями

💡 Скоро будет доступно больше настроек!"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def stats_cmd(update, context):
                self.stdout.write(f"Команда /stats от {update.effective_user.first_name}")
                try:
                    message = """📊 *МОЯ СТАТИСТИКА*

☕ *Тайный кофе:*
   └ Встреч: 0
   └ Рейтинг: новичок

🎯 *Активности:*
   └ Участий: 0
   └ Очков: 0

📈 *Общее:*
   └ Дней в системе: 1
   └ Активность: начинающий

💡 Участвуйте в активностях для роста статистики!"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def preferences_cmd(update, context):
                self.stdout.write(f"Команда /preferences от {update.effective_user.first_name}")
                try:
                    message = """☕ *НАСТРОЙКИ ТАЙНОГО КОФЕ*

� Доступность: не настроено
💻 Формат встреч: не указан
🎯 Темы интересов: не выбраны

⚙️ Используйте кнопки ниже для настройки:
• Укажите удобное время
• Выберите формат (онлайн/оффлайн)
• Отметьте интересные темы

💡 Настройки помогут найти подходящего собеседника!"""
                    await reply_with_footer(update, message, parse_mode='Markdown')
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")

            async def test_cmd(update, context):
                self.stdout.write(f"Команда /test от {update.effective_user.first_name}")
                try:
                    await reply_with_footer(update, "✅ Тест прошел! Все команды работают корректно.")
                    self.stdout.write("✅ Ответ отправлен")
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка ответа: {e}")
            
            # Регистрируем все обработчики
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_cmd))
            app.add_handler(CommandHandler("menu", help_cmd))  # menu = help
            app.add_handler(CommandHandler("coffee", coffee_cmd))
            app.add_handler(CommandHandler("activities", activities_cmd))
            app.add_handler(CommandHandler("profile", profile_cmd))
            app.add_handler(CommandHandler("settings", settings_cmd))
            app.add_handler(CommandHandler("stats", stats_cmd))
            app.add_handler(CommandHandler("preferences", preferences_cmd))
            app.add_handler(CommandHandler("test", test_cmd))
            
            self.stdout.write('✅ Обработчики добавлены')
            self.stdout.write('🚀 Запуск polling...')
            
            # Простой запуск polling
            app.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановка по Ctrl+C'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
            import traceback
            traceback.print_exc()