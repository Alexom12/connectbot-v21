"""
Redis utilities for ConnectBot v21
Совместимый адаптер для новой Redis интеграции
"""
import json
import logging
from typing import Any, Optional
from django.core.cache import cache
from django.conf import settings

# Импортируем новую интеграцию
from .redis_integration import redis_integration, get_user_temp_manager

logger = logging.getLogger(__name__)


class RedisManager:
    """Менеджер для работы с Redis кешем"""
    
    # Префиксы для разных типов данных
    PREFIX_EMPLOYEE = "emp:"
    PREFIX_ACTIVITY = "act:"
    PREFIX_INTERESTS = "int:"
    PREFIX_SESSION = "sess:"
    
    @staticmethod
    def get_employee_cache_key(employee_id: int) -> str:
        """Получить ключ кеша для сотрудника"""
        return f"{RedisManager.PREFIX_EMPLOYEE}{employee_id}"
    
    @staticmethod
    def get_activity_cache_key(activity_id: int) -> str:
        """Получить ключ кеша для активности"""
        return f"{RedisManager.PREFIX_ACTIVITY}{activity_id}"
    
    @staticmethod
    def get_interests_cache_key(employee_id: int) -> str:
        """Получить ключ кеша для интересов сотрудника"""
        return f"{RedisManager.PREFIX_INTERESTS}{employee_id}"
    
    @staticmethod
    def cache_employee_data(employee_id: int, data: dict, timeout: int = 3600) -> bool:
        """
        Кешировать данные сотрудника
        
        Args:
            employee_id: ID сотрудника
            data: Данные для кеширования
            timeout: Время жизни кеша в секундах (по умолчанию 1 час)
        
        Returns:
            bool: Успешность операции
        """
        try:
            key = RedisManager.get_employee_cache_key(employee_id)
            cache.set(key, data, timeout)
            logger.debug(f"Cached employee data for ID {employee_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache employee data: {e}")
            return False
    
    @staticmethod
    def get_employee_data(employee_id: int) -> Optional[dict]:
        """
        Получить данные сотрудника из кеша
        
        Args:
            employee_id: ID сотрудника
        
        Returns:
            dict или None: Данные сотрудника или None если не найдены
        """
        try:
            key = RedisManager.get_employee_cache_key(employee_id)
            data = cache.get(key)
            if data:
                logger.debug(f"Retrieved employee data from cache for ID {employee_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to get employee data from cache: {e}")
            return None
    
    @staticmethod
    def cache_employee_interests(employee_id: int, interests: list, timeout: int = 1800) -> bool:
        """
        Кешировать интересы сотрудника
        
        Args:
            employee_id: ID сотрудника
            interests: Список интересов
            timeout: Время жизни кеша в секундах (по умолчанию 30 минут)
        
        Returns:
            bool: Успешность операции
        """
        try:
            key = RedisManager.get_interests_cache_key(employee_id)
            cache.set(key, interests, timeout)
            logger.debug(f"Cached interests for employee ID {employee_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache employee interests: {e}")
            return False
    
    @staticmethod
    def get_employee_interests(employee_id: int) -> Optional[list]:
        """
        Получить интересы сотрудника из кеша
        
        Args:
            employee_id: ID сотрудника
        
        Returns:
            list или None: Список интересов или None если не найдены
        """
        try:
            key = RedisManager.get_interests_cache_key(employee_id)
            interests = cache.get(key)
            if interests:
                logger.debug(f"Retrieved interests from cache for employee ID {employee_id}")
            return interests
        except Exception as e:
            logger.error(f"Failed to get employee interests from cache: {e}")
            return None
    
    @staticmethod
    def invalidate_employee_cache(employee_id: int) -> bool:
        """
        Очистить все кешированные данные сотрудника
        
        Args:
            employee_id: ID сотрудника
        
        Returns:
            bool: Успешность операции
        """
        try:
            employee_key = RedisManager.get_employee_cache_key(employee_id)
            interests_key = RedisManager.get_interests_cache_key(employee_id)
            
            cache.delete(employee_key)
            cache.delete(interests_key)
            
            logger.debug(f"Invalidated cache for employee ID {employee_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate employee cache: {e}")
            return False
    
    @staticmethod
    async def async_invalidate_employee_cache(employee_id: int) -> bool:
        """
        Асинхронно очистить все кешированные данные сотрудника
        
        Args:
            employee_id: ID сотрудника
        
        Returns:
            bool: Успешность операции
        """
        from asgiref.sync import sync_to_async
        return await sync_to_async(RedisManager.invalidate_employee_cache)(employee_id)
    
    @staticmethod
    def cache_activity_participants(activity_id: int, participants: list, timeout: int = 900) -> bool:
        """
        Кешировать участников активности
        
        Args:
            activity_id: ID активности
            participants: Список участников
            timeout: Время жизни кеша в секундах (по умолчанию 15 минут)
        
        Returns:
            bool: Успешность операции
        """
        try:
            key = f"{RedisManager.PREFIX_ACTIVITY}{activity_id}:participants"
            cache.set(key, participants, timeout)
            logger.debug(f"Cached participants for activity ID {activity_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache activity participants: {e}")
            return False
    
    @staticmethod
    def get_activity_participants(activity_id: int) -> Optional[list]:
        """
        Получить участников активности из кеша
        
        Args:
            activity_id: ID активности
        
        Returns:
            list или None: Список участников или None если не найдены
        """
        try:
            key = f"{RedisManager.PREFIX_ACTIVITY}{activity_id}:participants"
            participants = cache.get(key)
            if participants:
                logger.debug(f"Retrieved participants from cache for activity ID {activity_id}")
            return participants
        except Exception as e:
            logger.error(f"Failed to get activity participants from cache: {e}")
            return None
    
    @staticmethod
    def store_bot_session(user_id: int, session_data: dict, timeout: int = 7200) -> bool:
        """
        Сохранить сессию бота для пользователя
        
        Args:
            user_id: Telegram ID пользователя
            session_data: Данные сессии
            timeout: Время жизни сессии в секундах (по умолчанию 2 часа)
        
        Returns:
            bool: Успешность операции
        """
        try:
            key = f"{RedisManager.PREFIX_SESSION}{user_id}"
            cache.set(key, session_data, timeout)
            logger.debug(f"Stored bot session for user ID {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store bot session: {e}")
            return False
    
    @staticmethod
    def get_bot_session(user_id: int) -> Optional[dict]:
        """
        Получить сессию бота для пользователя
        
        Args:
            user_id: Telegram ID пользователя
        
        Returns:
            dict или None: Данные сессии или None если не найдены
        """
        try:
            key = f"{RedisManager.PREFIX_SESSION}{user_id}"
            session_data = cache.get(key)
            if session_data:
                logger.debug(f"Retrieved bot session for user ID {user_id}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to get bot session: {e}")
            return None
    
    @staticmethod
    def clear_bot_session(user_id: int) -> bool:
        """
        Очистить сессию бота для пользователя
        
        Args:
            user_id: Telegram ID пользователя
        
        Returns:
            bool: Успешность операции
        """
        try:
            key = f"{RedisManager.PREFIX_SESSION}{user_id}"
            cache.delete(key)
            logger.debug(f"Cleared bot session for user ID {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear bot session: {e}")
            return False
    
    @staticmethod
    def is_redis_available() -> bool:
        """
        Проверить доступность Redis
        
        Returns:
            bool: True если Redis доступен
        """
        try:
            health_info = redis_integration.health_check()
            return health_info.get('redis_available', False)
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False


# Новые методы с использованием улучшенной интеграции
class EnhancedRedisManager(RedisManager):
    """Расширенный менеджер Redis с новыми возможностями"""
    
    @staticmethod
    def cache_user_menu(user_id: int, menu_data: dict, menu_type: str = 'main') -> bool:
        """Кэширует меню пользователя"""
        return redis_integration.menu_cache.set_user_menu(user_id, menu_data, menu_type)
    
    @staticmethod
    def get_user_menu(user_id: int, menu_type: str = 'main') -> Optional[dict]:
        """Получает кэшированное меню пользователя"""
        return redis_integration.menu_cache.get_user_menu(user_id, menu_type)
    
    @staticmethod
    def store_user_conversation_state(user_id: int, state_data: dict) -> bool:
        """Сохраняет состояние разговора пользователя"""
        user_manager = get_user_temp_manager(user_id)
        return user_manager.store_conversation_state(state_data)
    
    @staticmethod
    def get_user_conversation_state(user_id: int) -> Optional[dict]:
        """Получает состояние разговора пользователя"""
        user_manager = get_user_temp_manager(user_id)
        return user_manager.get_conversation_state()
    
    @staticmethod
    def publish_user_event(user_id: int, event_type: str, data: dict) -> bool:
        """Публикует событие пользователя"""
        return redis_integration.events.publish_user_event(user_id, event_type, data)
    
    @staticmethod
    def get_redis_health() -> dict:
        """Получает полную информацию о состоянии Redis"""
        return redis_integration.health_check()
    
    @staticmethod
    def clear_user_cache(user_id: int) -> bool:
        """Очищает весь кэш пользователя"""
        # Используем старый метод + новые возможности
        success = RedisManager.invalidate_employee_cache(user_id)
        redis_integration.menu_cache.clear_user_all_menus(user_id)
        
        # Публикуем событие очистки
        redis_integration.events.publish_user_event(
            user_id, 'user.cache_cleared', {'timestamp': cache.get('cache_timestamp', 0)}
        )
        
        return success