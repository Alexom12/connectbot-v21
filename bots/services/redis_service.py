"""
Сервис для работы с Redis кэшем
"""
import logging
import redis
import urllib.parse
from django.conf import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Сервис для работы с Redis"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Подключение к Redis"""
        try:
            # Пытаемся распарсить REDIS_URL из настройки, если она есть
            redis_url = getattr(settings, 'REDIS_URL', None) or ''
            host = 'localhost'
            port = 6379
            db = 0
            if redis_url:
                try:
                    parsed = urllib.parse.urlparse(redis_url)
                    host = parsed.hostname or host
                    port = parsed.port or port
                    # путь вида /0
                    if parsed.path:
                        try:
                            db = int(parsed.path.lstrip('/'))
                        except Exception:
                            db = 0
                except Exception:
                    # fallback to defaults
                    host = 'localhost'
                    port = 6379

            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            # Проверяем подключение
            self.redis_client.ping()
            logger.info("Подключение к Redis успешно")
            
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}")
            self.redis_client = None
    
    def is_available(self):
        """Проверка доступности Redis"""
        return self.redis_client is not None
    
    def set_cache(self, key, value, expire=3600):
        """Сохранение значения в кэше"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.setex(key, expire, value)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    def get_cache(self, key):
        """Получение значения из кэша"""
        if not self.is_available():
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    def delete_cache(self, key):
        """Удаление значения из кэша"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False

# Создаем экземпляр сервиса
redis_service = RedisService()