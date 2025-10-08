"""
Основной модуль Telegram бота ConnectBot
"""
import asyncio
import logging
from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ConnectBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        try:
            # Поиск сотрудника в базе
            employee = await self.find_employee_by_user(user)
            
            if employee:
                await update.message.reply_text(
                    f"Добро пожаловать, {employee.full_name}! 🎉\n"
                    "Вы успешно авторизованы в ConnectBot."
                )
                # Здесь будет переход к настройке предпочтений
            else:
                await update.message.reply_text(
                    "🔐 *Доступ к ConnectBot ограничен*\n\n"
                    "Для использования бота необходимо быть сотрудником компании.\n"
                    "Если вы сотрудник, но не можете войти, обратитесь к администратору."
                )
                
        except Exception as e:
            logger.error(f"Ошибка в команде /start: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    
    @sync_to_async
    def find_employee_by_user(self, user):
        """Поиск сотрудника по данным Telegram пользователя"""
        from employees.models import Employee
        
        username = user.username
        
        if not username:
            return None
        
        # Нормализация username
        normalized_username = self.normalize_username(username)
        
        try:
            # Поиск по точному совпадению
            employee = Employee.objects.filter(
                telegram_username__iexact=username
            ).first()
            
            if employee:
                # Обновляем telegram_id если нужно
                if not employee.telegram_id:
                    employee.telegram_id = user.id
                    employee.save()
                return employee
            
            # Relaxed matching поиск
            employees = Employee.objects.all()
            matches = []
            
            for emp in employees:
                if emp.telegram_username:
                    emp_normalized = self.normalize_username(emp.telegram_username)
                    if emp_normalized == normalized_username:
                        matches.append(emp)
            
            if len(matches) == 1:
                employee = matches[0]
                if not employee.telegram_id:
                    employee.telegram_id = user.id
                    employee.save()
                return employee
                
        except Exception as e:
            logger.error(f"Ошибка поиска сотрудника: {e}")
            
        return None
    
    def normalize_username(self, username):
        """Нормализация username для поиска"""
        if not username:
            return ""
        return username.strip().lstrip('@').lower().replace('_', '').replace('-', '').replace('.', '')
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        # Здесь будут добавлены другие обработчики
    
    async def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN не установлен")
            return
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        logger.info("Бот запущен и ожидает сообщений...")
        await self.application.run_polling()

def main():
    """Основная функция запуска бота"""
    bot = ConnectBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()
