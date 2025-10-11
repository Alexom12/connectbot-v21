import json
import logging
from django.core.cache import cache
from config.settings import CACHE_TTL

logger = logging.getLogger(__name__)

class ActivityRedisService:
    """Сервис для работы с Redis в модуле активностей"""
    
    async def cache_activity_data(self, activity_type, data):
        """Кэширование данных активности"""
        try:
            cache_key = f"activity_{activity_type}_data"
            cache.set(cache_key, json.dumps(data), CACHE_TTL['activities'])
            return True
        except Exception as e:
            logger.error(f"Ошибка кэширования данных активности: {e}")
            return False
    
    async def get_cached_activity_data(self, activity_type):
        """Получение кэшированных данных активности"""
        try:
            cache_key = f"activity_{activity_type}_data"
            data = cache.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения кэшированных данных: {e}")
            return None
    
    async def cache_user_activities(self, user_id, activities):
        """Кэширование активностей пользователя"""
        try:
            cache_key = f"user_{user_id}_activities"
            cache.set(cache_key, json.dumps(activities), CACHE_TTL['user_menu'])
            return True
        except Exception as e:
            logger.error(f"Ошибка кэширования активностей пользователя: {e}")
            return False
    
    async def get_cached_user_activities(self, user_id):
        """Получение кэшированных активностей пользователя"""
        try:
            cache_key = f"user_{user_id}_activities"
            data = cache.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения кэшированных активностей: {e}")
            return None

# Создаем экземпляр сервиса
activity_redis_service = ActivityRedisService()