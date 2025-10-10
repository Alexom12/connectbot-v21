"""
Главный модуль Redis интеграции для ConnectBot
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache

from .redis_menu_cache import MenuCache, MenuBuilder
from .redis_events import EventPublisher, EventSubscriber, ConnectBotEvents, event_publisher
from .redis_temp_data import TempDataManager, UserTempDataManager, get_user_temp_manager

logger = logging.getLogger(__name__)


class ConnectBotRedisIntegration:
    """Главный класс для работы с Redis в ConnectBot"""
    
    def __init__(self):
        self.menu_cache = MenuCache
        self.menu_builder = MenuBuilder
        self.temp_data = TempDataManager
        self.events = event_publisher
        self.event_types = ConnectBotEvents
    
    def get_user_manager(self, user_id: int) -> UserTempDataManager:
        """Получает менеджер данных пользователя"""
        return get_user_temp_manager(user_id)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверяет состояние Redis подключения
        
        Returns:
            Словарь с информацией о состоянии Redis
        """
        try:
            # Простая проверка доступности кэша
            test_key = 'health_check_test'
            test_value = 'ok'
            
            cache.set(test_key, test_value, 10)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            is_healthy = result == test_value
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'redis_available': is_healthy,
                'cache_backend': settings.CACHES['default']['BACKEND'],
                'redis_url': getattr(settings, 'REDIS_URL', 'not configured'),
                'java_service_url': getattr(settings, 'JAVA_SERVICE_URL', 'not configured'),
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'redis_available': False,
                'error': str(e),
                'cache_backend': getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', 'unknown'),
            }
    
    def clear_all_cache(self) -> bool:
        """
        Очищает весь кэш Redis
        
        Returns:
            True если успешно очищен
        """
        try:
            cache.clear()
            
            # Публикуем событие очистки кэша
            self.events.publish_global_event(
                self.event_types.CACHE_CLEARED,
                {'type': 'all_cache', 'cleared_at': cache.get('cache_timestamp', 0)}
            )
            
            logger.info("All Redis cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получает статистику использования кэша
        
        Returns:
            Словарь со статистикой
        """
        try:
            # Базовая статистика (в реальной Redis можно получить детальную информацию)
            stats = {
                'cache_backend': settings.CACHES['default']['BACKEND'],
                'cache_location': settings.CACHES['default']['LOCATION'],
                'default_timeout': settings.CACHES['default'].get('TIMEOUT', 300),
                'key_prefix': settings.CACHES['default'].get('KEY_PREFIX', ''),
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}


# Глобальный экземпляр интеграции
redis_integration = ConnectBotRedisIntegration()


# Утилиты для быстрого доступа
def get_redis_integration() -> ConnectBotRedisIntegration:
    """Получает экземпляр Redis интеграции"""
    return redis_integration


def cache_user_menu(user_id: int, menu_data: Dict[str, Any], menu_type: str = 'main') -> bool:
    """
    Быстрое кэширование меню пользователя
    
    Args:
        user_id: ID пользователя
        menu_data: Данные меню
        menu_type: Тип меню
    
    Returns:
        True если успешно закэшировано
    """
    return MenuCache.set_user_menu(user_id, menu_data, menu_type)


def get_cached_user_menu(user_id: int, menu_type: str = 'main') -> Optional[Dict[str, Any]]:
    """
    Быстрое получение кэшированного меню
    
    Args:
        user_id: ID пользователя
        menu_type: Тип меню
    
    Returns:
        Данные меню или None
    """
    return MenuCache.get_user_menu(user_id, menu_type)


def publish_user_action(user_id: int, action: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Быстрая публикация пользовательского действия
    
    Args:
        user_id: ID пользователя
        action: Действие пользователя
        data: Дополнительные данные
    
    Returns:
        True если успешно опубликовано
    """
    event_data = data or {}
    event_data['action'] = action
    
    return event_publisher.publish_user_event(
        user_id, 
        f'user.action.{action}', 
        event_data
    )


def store_user_temp_data(user_id: int, key: str, data: Any, minutes: int = 30) -> bool:
    """
    Быстрое сохранение временных данных пользователя
    
    Args:
        user_id: ID пользователя
        key: Ключ данных
        data: Данные для сохранения
        minutes: Время жизни в минутах
    
    Returns:
        True если успешно сохранено
    """
    user_manager = get_user_temp_manager(user_id)
    return user_manager.store(key, data, minutes * 60)


def get_user_temp_data(user_id: int, key: str, default: Any = None) -> Any:
    """
    Быстрое получение временных данных пользователя
    
    Args:
        user_id: ID пользователя
        key: Ключ данных
        default: Значение по умолчанию
    
    Returns:
        Данные или значение по умолчанию
    """
    user_manager = get_user_temp_manager(user_id)
    return user_manager.get(key, default)


# Декораторы для автоматического кэширования
def cache_result(timeout: int = 300, key_prefix: str = ''):
    """
    Декоратор для автоматического кэширования результатов функций
    
    Args:
        timeout: Время жизни кэша в секундах
        key_prefix: Префикс ключа кэша
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша на основе функции и аргументов
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Пытаемся получить из кэша
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            logger.debug(f"Cache set for {func.__name__}, timeout: {timeout}s")
            return result
        
        return wrapper
    return decorator


def invalidate_user_cache(user_id: int) -> bool:
    """
    Инвалидирует весь кэш пользователя
    
    Args:
        user_id: ID пользователя
    
    Returns:
        True если успешно очищен
    """
    try:
        # Очищаем меню
        MenuCache.clear_user_all_menus(user_id)
        
        # Публикуем событие очистки кэша
        event_publisher.publish_user_event(
            user_id,
            ConnectBotEvents.CACHE_CLEARED,
            {'type': 'user_cache', 'user_id': user_id}
        )
        
        logger.info(f"User cache invalidated for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error invalidating user cache for {user_id}: {e}")
        return False