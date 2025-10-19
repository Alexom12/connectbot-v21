"""
Django settings for ConnectBot project
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = []

# Telegram Bot Token
try:
    with open('telegram_token.txt', 'r') as f:
        TELEGRAM_TOKEN = f.read().strip()
except FileNotFoundError:
    TELEGRAM_TOKEN = None


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'django_apscheduler',

    # Custom apps
    'employees',
    'bots.apps.BotsConfig',
    'activities',  # Добавлено новое приложение для активностей
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

# Redis Configuration
REDIS_URL = config('REDIS_URL', default='redis://redis:6379/0')

# Java Service Configuration
MATCHING_SERVICE_URL = config('MATCHING_SERVICE_URL_INTERNAL', default='http://localhost:8080')
MATCHING_SERVICE_TIMEOUT = config('MATCHING_SERVICE_TIMEOUT', default=15, cast=int)


# Secret token for /metrics/trigger endpoint (empty by default — disabled in prod)
METRICS_TRIGGER_TOKEN = config('METRICS_TRIGGER_TOKEN', default='')

# Cache Configuration with Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'connectbot',
        'TIMEOUT': 300,
    }
}

# Session engine - use Redis for session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
SUPER_ADMIN_ID = config('SUPER_ADMIN_ID', default=0, cast=int)

# Service-to-service auth token for Data API
def _read_secret_file(path):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        pass
    return None

# Try to load SECRET_KEY and SERVICE_AUTH_TOKEN from Docker secrets if available
secret_key_from_file = _read_secret_file('/run/secrets/django_secret_key')
if secret_key_from_file:
    SECRET_KEY = secret_key_from_file
else:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')

service_token_from_file = _read_secret_file('/run/secrets/service_auth_token')
if service_token_from_file:
    SERVICE_AUTH_TOKEN = service_token_from_file
else:
    SERVICE_AUTH_TOKEN = config('SERVICE_AUTH_TOKEN', default='')

# Admin settings
ADMIN_USERNAME = config('ADMIN_USERNAME', default='hr_admin')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='hr@company.com')

# ConnectBot Settings
CONNECTBOT_SETTINGS = {
    'AUTO_SCHEDULE_ACTIVITIES': True,
    'DEFAULT_TIMEZONE': 'Europe/Moscow',
    'MAX_PARTICIPANTS_PER_ACTIVITY': 2,
    'NOTIFICATION_HOUR': 10,  # 10:00 AM
    'WEEKLY_SCHEDULE_DAY': 2,  # Tuesday (0=Monday, 6=Sunday)
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'bot.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'bots': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'employees': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'activities': {  # Добавлен логгер для activities
            'handlers': ['file', 'console', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Email settings (for future notifications)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@company.com')

# Cache timeout settings
CACHE_TTL = {
    'default': 300,  # 5 minutes
    'user_menu': 1800,  # 30 minutes
    'user_profile': 3600,  # 1 hour
    'activities': 900,  # 15 minutes
    'temporary_data': 1800,  # 30 minutes
}

# Internationalization
LANGUAGES = [
    ('ru', 'Russian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Custom settings for ConnectBot
BOT_SETTINGS = {
    'ADMIN_COMMANDS': ['/admin', '/admin_help', '/admins', '/add_admin', '/remove_admin'],
    'USER_COMMANDS': ['/start', '/menu', '/preferences', '/help', '/profile'],
    'INTERESTS': {
        'coffee': '☕️ Тайный кофе',
        'lunch': '🍝 Обед вслепую',
        'walk': '🚶 Слепая прогулка',
        'chess': '♟️ Шахматы',
        'pingpong': '🏓 Настольный теннис',
        'games': '🎲 Настольные игры',
        'photo': '📸 Фотоквесты',
        'masterclass': '🧠 Мастер-классы',
        'clubs': '📚 Клубы по интересам',
    },
    'ACTIVITY_FREQUENCIES': {
        'coffee': 'weekly',
        'lunch': 'weekly',
        'walk': 'biweekly',
        'chess': 'weekly',
        'pingpong': 'weekly',
        'games': 'monthly',
        'photo': 'monthly',
        'masterclass': 'monthly',
        'clubs': 'ongoing',
    }
}