import os
import json
from pathlib import Path

def create_project_structure():
    """Создает полную структуру проекта ConnectBot v21"""
    
    # Корневая директория проекта
    project_root = Path("E:/ConnectBot v21")
    project_root.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Создание структуры проекта ConnectBot v21...")
    
    # Структура папок
    directories = [
        "venv",
        "config",
        "bots/management/commands",
        "bots/migrations",
        "employees/migrations", 
        "employees/management/commands",
        "scripts",
        "static/css",
        "static/js",
        "static/images",
        "templates/admin",
        "templates/bots",
        "data/import",
        "data/export",
        "logs",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    # Создаем папки
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана папка: {directory}")
    
    # Создаем файлы
    create_manage_py(project_root)
    create_requirements(project_root)
    create_env_file(project_root)
    create_vscode_settings(project_root)
    create_config_files(project_root)
    create_bot_files(project_root)
    create_employee_files(project_root)
    create_script_files(project_root)
    create_gitignore(project_root)
    
    print("\n✅ Структура проекта успешно создана!")
    print("📍 Расположение: E:/ConnectBot v21/")

def create_manage_py(project_root):
    """Создает manage.py"""
    content = '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
'''
    file_path = project_root / "manage.py"
    file_path.write_text(content, encoding='utf-8')
    print("📄 Создан файл: manage.py")

def create_requirements(project_root):
    """Создает requirements.txt"""
    content = '''Django>=4.2,<5.0
python-telegram-bot==20.7
apscheduler==3.10.4
pandas>=1.5.0
python-dotenv>=1.0.0
asgiref>=3.7.0
setuptools<81
openpyxl>=3.0.0
python-decouple>=3.8
'''
    file_path = project_root / "requirements.txt"
    file_path.write_text(content, encoding='utf-8')
    print("📄 Создан файл: requirements.txt")

def create_env_file(project_root):
    """Создает .env файл"""
    content = '''# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-12345

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Encoding
PYTHONIOENCODING=utf-8

# Admin
SUPER_ADMIN_ID=123456789
'''
    file_path = project_root / ".env"
    file_path.write_text(content, encoding='utf-8')
    print("📄 Создан файл: .env")

def create_vscode_settings(project_root):
    """Создает настройки VS Code"""
    settings = {
        "python.defaultInterpreterPath": "E:\\\\ConnectBot v21\\\\venv\\\\Scripts\\\\python.exe",
        "python.envFile": "${workspaceFolder}\\.env",
        "python.terminal.activateEnvironment": True,
        "files.autoSave": "afterDelay",
        "editor.formatOnSave": True,
        "python.analysis.extraPaths": [
            "./bots",
            "./employees"
        ],
        "[python]": {
            "editor.defaultFormatter": "ms-python.python",
            "editor.tabSize": 4,
            "editor.insertSpaces": True,
            "editor.codeActionsOnSave": {
                "source.organizeImports": True
            }
        }
    }
    
    vscode_dir = project_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(json.dumps(settings, indent=4, ensure_ascii=False), encoding='utf-8')
    print("📄 Создан файл: .vscode/settings.json")

def create_config_files(project_root):
    """Создает конфигурационные файлы Django"""
    
    # __init__.py для config
    init_file = project_root / "config" / "__init__.py"
    init_file.write_text("", encoding='utf-8')
    
    # settings.py
    settings_content = '''"""
Django settings for ConnectBot project
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'employees',
    'bots',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
SUPER_ADMIN_ID = config('SUPER_ADMIN_ID', default=0, cast=int)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'bot.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
'''
    settings_file = project_root / "config" / "settings.py"
    settings_file.write_text(settings_content, encoding='utf-8')
    print("📄 Создан файл: config/settings.py")
    
    # urls.py
    urls_content = '''"""
URL configuration for ConnectBot project.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
'''
    urls_file = project_root / "config" / "urls.py"
    urls_file.write_text(urls_content, encoding='utf-8')
    print("📄 Создан файл: config/urls.py")

def create_bot_files(project_root):
    """Создает файлы для модуля bots"""
    
    # __init__.py файлы
    init_paths = [
        "bots/__init__.py",
        "bots/management/__init__.py", 
        "bots/management/commands/__init__.py",
        "bots/migrations/__init__.py"
    ]
    
    for init_path in init_paths:
        file_path = project_root / init_path
        file_path.write_text("", encoding='utf-8')
    
    # runbot.py
    runbot_content = '''"""
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
                    f"Добро пожаловать, {employee.full_name}! 🎉\\n"
                    "Вы успешно авторизованы в ConnectBot."
                )
                # Здесь будет переход к настройке предпочтений
            else:
                await update.message.reply_text(
                    "🔐 *Доступ к ConnectBot ограничен*\\n\\n"
                    "Для использования бота необходимо быть сотрудником компании.\\n"
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
'''
    runbot_file = project_root / "bots" / "management" / "commands" / "runbot.py"
    runbot_file.write_text(runbot_content, encoding='utf-8')
    print("📄 Создан файл: bots/management/commands/runbot.py")

def create_employee_files(project_root):
    """Создает файлы для модуля employees"""
    
    # __init__.py файлы
    init_paths = [
        "employees/__init__.py",
        "employees/management/__init__.py",
        "employees/management/commands/__init__.py", 
        "employees/migrations/__init__.py"
    ]
    
    for init_path in init_paths:
        file_path = project_root / init_path
        file_path.write_text("", encoding='utf-8')
    
    # models.py
    models_content = '''"""
Модели для модуля сотрудников
"""
from django.db import models

class Employee(models.Model):
    """Модель сотрудника"""
    
    # Основная информация
    full_name = models.CharField("ФИО", max_length=200)
    position = models.CharField("Должность", max_length=200, blank=True, null=True)
    department = models.CharField("Отдел", max_length=200, blank=True, null=True)
    business_center = models.CharField("Бизнес-центр", max_length=100, blank=True, null=True)
    
    # Telegram данные
    telegram_id = models.BigIntegerField("Telegram ID", unique=True, blank=True, null=True)
    telegram_username = models.CharField("Telegram username", max_length=100, blank=True, null=True)
    
    # Дополнительная информация
    birth_date = models.DateField("Дата рождения", blank=True, null=True)
    is_active = models.BooleanField("Активный", default=True)
    
    # Даты
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.position or 'Нет должности'})"

class Interest(models.Model):
    """Модель интересов/активностей"""
    
    INTEREST_TYPES = [
        ('coffee', '☕️ Тайный кофе'),
        ('lunch', '🍝 Обед вслепую'),
        ('walk', '🚶 Слепая прогулка'),
        ('chess', '♟️ Шахматы'),
        ('pingpong', '🏓 Настольный теннис'),
        ('games', '🎲 Настольные игры'),
        ('photo', '📸 Фотоквесты'),
        ('masterclass', '🧠 Мастер-классы'),
        ('clubs', '📚 Клубы по интересам'),
    ]
    
    code = models.CharField("Код", max_length=20, choices=INTEREST_TYPES, unique=True)
    name = models.CharField("Название", max_length=100)
    emoji = models.CharField("Эмодзи", max_length=10)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активный", default=True)
    
    class Meta:
        verbose_name = "Интерес"
        verbose_name_plural = "Интересы"
    
    def __str__(self):
        return f"{self.emoji} {self.name}"

class EmployeeInterest(models.Model):
    """Связь сотрудника с интересами"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    
    class Meta:
        verbose_name = "Интерес сотрудника"
        verbose_name_plural = "Интересы сотрудников"
        unique_together = ['employee', 'interest']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.interest.name}"
'''
    models_file = project_root / "employees" / "models.py"
    models_file.write_text(models_content, encoding='utf-8')
    print("📄 Создан файл: employees/models.py")

def create_script_files(project_root):
    """Создает скрипты для управления проектом"""
    
    # start_services.ps1
    ps_script = '''# PowerShell скрипт для запуска сервисов ConnectBot

Write-Host "🚀 Запуск ConnectBot сервисов..." -ForegroundColor Green

# Проверка существования виртуального окружения
$venvPath = "E:\\ConnectBot v21\\venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "❌ Виртуальное окружение не найдено" -ForegroundColor Red
    Write-Host "Создайте виртуальное окружение: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Активация виртуального окружения
$activateScript = "$venvPath\\Scripts\\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "❌ Скрипт активации не найден" -ForegroundColor Red
    exit 1
}

# Применение миграций
Write-Host "📦 Применение миграций..." -ForegroundColor Yellow
python manage.py migrate

# Запуск Django сервера
Write-Host "🌐 Запуск Django сервера..." -ForegroundColor Cyan
Start-Process python -ArgumentList "manage.py", "runserver" -NoNewWindow

# Запуск Telegram бота
Write-Host "🤖 Запуск Telegram бота..." -ForegroundColor Cyan
Start-Process python -ArgumentList "manage.py", "runbot" -NoNewWindow

Write-Host "✅ Все сервисы запущены!" -ForegroundColor Green
Write-Host "• Django admin: http://localhost:8000/admin/" -ForegroundColor Gray
Write-Host "• Бот активен и ожидает сообщений" -ForegroundColor Gray
'''
    ps_file = project_root / "scripts" / "start_services.ps1"
    ps_file.write_text(ps_script, encoding='utf-8')
    print("📄 Создан файл: scripts/start_services.ps1")

def create_gitignore(project_root):
    """Создает .gitignore файл"""
    gitignore_content = '''# Django
*.log
*.pot
*.pyc
__pycache__/
local_settings.py
db.sqlite3
media/

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/*.log
bot.log
bot.err

# Data
data/import/*.xlsx
data/export/*.csv

# Environment variables
.env
'''
    gitignore_file = project_root / ".gitignore"
    gitignore_file.write_text(gitignore_content, encoding='utf-8')
    print("📄 Создан файл: .gitignore")

if __name__ == "__main__":
    create_project_structure()