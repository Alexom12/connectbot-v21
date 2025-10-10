"""
Redis кэширование для меню пользователей
"""
import json
import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class MenuCache:
    """Утилиты для кэширования меню пользователей в Redis"""
    
    CACHE_PREFIX = 'menu'
    DEFAULT_TIMEOUT = getattr(settings, 'CACHE_TTL', {}).get('user_menu', 1800)  # 30 minutes
    
    @classmethod
    def _get_cache_key(cls, user_id: int, menu_type: str = 'main') -> str:
        """Генерирует ключ кэша для пользователя"""
        return f"{cls.CACHE_PREFIX}:user:{user_id}:{menu_type}"
    
    @classmethod
    def get_user_menu(cls, user_id: int, menu_type: str = 'main') -> Optional[Dict[str, Any]]:
        """
        Получает меню пользователя из кэша
        
        Args:
            user_id: ID пользователя
            menu_type: Тип меню (main, preferences, activities)
        
        Returns:
            Данные меню или None если не найдено
        """
        try:
            cache_key = cls._get_cache_key(user_id, menu_type)
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.debug(f"Menu cache hit for user {user_id}, type {menu_type}")
                return json.loads(cached_data) if isinstance(cached_data, str) else cached_data
            
            logger.debug(f"Menu cache miss for user {user_id}, type {menu_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting menu from cache for user {user_id}: {e}")
            return None
    
    @classmethod
    def set_user_menu(cls, user_id: int, menu_data: Dict[str, Any], 
                      menu_type: str = 'main', timeout: Optional[int] = None) -> bool:
        """
        Сохраняет меню пользователя в кэш
        
        Args:
            user_id: ID пользователя
            menu_data: Данные меню для кэширования
            menu_type: Тип меню
            timeout: Время жизни кэша в секундах
        
        Returns:
            True если успешно сохранено
        """
        try:
            cache_key = cls._get_cache_key(user_id, menu_type)
            timeout = timeout or cls.DEFAULT_TIMEOUT
            
            # Добавляем метаданные
            cache_data = {
                'data': menu_data,
                'user_id': user_id,
                'menu_type': menu_type,
                'cached_at': cache.get('cache_timestamp', 0),
            }
            
            cache.set(cache_key, json.dumps(cache_data), timeout)
            logger.debug(f"Menu cached for user {user_id}, type {menu_type}, timeout {timeout}s")
            return True
            
        except Exception as e:
            logger.error(f"Error caching menu for user {user_id}: {e}")
            return False
    
    @classmethod
    def delete_user_menu(cls, user_id: int, menu_type: str = 'main') -> bool:
        """
        Удаляет меню пользователя из кэша
        
        Args:
            user_id: ID пользователя
            menu_type: Тип меню для удаления
        
        Returns:
            True если успешно удалено
        """
        try:
            cache_key = cls._get_cache_key(user_id, menu_type)
            cache.delete(cache_key)
            logger.debug(f"Menu cache cleared for user {user_id}, type {menu_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting menu cache for user {user_id}: {e}")
            return False
    
    @classmethod
    def clear_user_all_menus(cls, user_id: int) -> bool:
        """
        Очищает все меню пользователя из кэша
        
        Args:
            user_id: ID пользователя
        
        Returns:
            True если успешно очищено
        """
        try:
            menu_types = ['main', 'preferences', 'activities', 'admin']
            for menu_type in menu_types:
                cls.delete_user_menu(user_id, menu_type)
            
            logger.info(f"All menu cache cleared for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all menus for user {user_id}: {e}")
            return False
    
    @classmethod
    def get_cached_users(cls) -> List[int]:
        """
        Получает список всех пользователей с кэшированными меню
        
        Returns:
            Список ID пользователей
        """
        try:
            # Это приблизительный метод - в реальном Redis нужно использовать SCAN
            # Для демонстрации возвращаем пустой список
            logger.debug("Getting cached users list")
            return []
            
        except Exception as e:
            logger.error(f"Error getting cached users: {e}")
            return []
    
    @classmethod
    def refresh_user_menu(cls, user_id: int, menu_type: str = 'main') -> bool:
        """
        Обновляет время жизни кэша меню пользователя
        
        Args:
            user_id: ID пользователя
            menu_type: Тип меню
        
        Returns:
            True если успешно обновлено
        """
        try:
            menu_data = cls.get_user_menu(user_id, menu_type)
            if menu_data:
                cls.set_user_menu(user_id, menu_data.get('data', {}), menu_type)
                logger.debug(f"Menu cache refreshed for user {user_id}, type {menu_type}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error refreshing menu cache for user {user_id}: {e}")
            return False


class MenuBuilder:
    """Строитель меню с поддержкой кэширования"""
    
    @classmethod
    def build_main_menu(cls, user_id: int, user_role: str = 'user') -> Dict[str, Any]:
        """
        Строит главное меню для пользователя
        
        Args:
            user_id: ID пользователя
            user_role: Роль пользователя (user, admin, super_admin)
        
        Returns:
            Данные главного меню
        """
        # Проверяем кэш
        cached_menu = MenuCache.get_user_menu(user_id, 'main')
        if cached_menu and cached_menu.get('data'):
            return cached_menu['data']
        
        # Строим меню
        menu_data = {
            'type': 'main',
            'user_id': user_id,
            'role': user_role,
            'options': []
        }
        
        # Основные опции для всех пользователей
        menu_data['options'].extend([
            {'key': 'profile', 'label': '👤 Профиль', 'action': 'show_profile'},
            {'key': 'activities', 'label': '🎯 Мои активности', 'action': 'show_activities'},
            {'key': 'preferences', 'label': '⚙️ Настройки', 'action': 'show_preferences'},
        ])
        
        # Опции для администраторов
        if user_role in ['admin', 'super_admin']:
            menu_data['options'].extend([
                {'key': 'admin_panel', 'label': '🔧 Админ панель', 'action': 'admin_panel'},
                {'key': 'manage_users', 'label': '👥 Управление пользователями', 'action': 'manage_users'},
            ])
        
        # Кэшируем меню
        MenuCache.set_user_menu(user_id, menu_data, 'main')
        
        return menu_data
    
    @classmethod
    def build_preferences_menu(cls, user_id: int) -> Dict[str, Any]:
        """Строит меню настроек для пользователя"""
        # Проверяем кэш
        cached_menu = MenuCache.get_user_menu(user_id, 'preferences')
        if cached_menu and cached_menu.get('data'):
            return cached_menu['data']
        
        # Строим меню настроек
        menu_data = {
            'type': 'preferences',
            'user_id': user_id,
            'options': [
                {'key': 'interests', 'label': '❤️ Интересы', 'action': 'edit_interests'},
                {'key': 'notifications', 'label': '🔔 Уведомления', 'action': 'edit_notifications'},
                {'key': 'privacy', 'label': '🔒 Приватность', 'action': 'edit_privacy'},
                {'key': 'back', 'label': '⬅️ Назад', 'action': 'main_menu'},
            ]
        }
        
        # Кэшируем меню
        MenuCache.set_user_menu(user_id, menu_data, 'preferences')
        
        return menu_data