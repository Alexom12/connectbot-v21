"""
Исправленная версия бота с улучшенными настройками подключения
"""
import asyncio
import logging
import ssl
import os
import sys
from pathlib import Path

# Настройка Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from asgiref.sync import sync_to_async
import httpx

from employees.utils import AuthManager, PreferenceManager
from employees.redis_utils import RedisManager
from bots.menu_manager import MenuManager
from bots.utils.message_utils import reply_with_footer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ConnectBotFixed:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None
        self.redis_available = RedisManager.is_redis_available()

        if self.redis_available:
            logger.info("✅ Redis доступен, включено кеширование сессий")
        else:
            logger.warning("⚠️ Redis не доступен, кеширование сессий отключено")

    def create_custom_request(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=30.0,
                read=30.0,
                write=30.0,
                pool=30.0
            ),
            verify=False,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=30)
        )
        return HTTPXRequest(http_version="1.1", client=httpx_client)

    def run(self):
        try:
            custom_request = self.create_custom_request()
            self.application = Application.builder().token(self.token).request(custom_request).build()
            self.setup_handlers()
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)

if __name__ == '__main__':
    bot = ConnectBotFixed()
    bot.run()