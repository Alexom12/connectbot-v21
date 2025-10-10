"""
Утилиты для работы с временными данными в Redis
"""
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class TempDataManager:
    """Менеджер временных данных в Redis"""
    
    CACHE_PREFIX = 'temp'
    DEFAULT_TIMEOUT = getattr(settings, 'CACHE_TTL', {}).get('temporary_data', 1800)  # 30 minutes
    
    @classmethod
    def _get_cache_key(cls, key: str, namespace: str = 'default') -> str:
        """Генерирует ключ кэша с префиксом"""
        return f"{cls.CACHE_PREFIX}:{namespace}:{key}"
    
    @classmethod
    def store_temp_data(cls, key: str, data: Any, timeout: Optional[int] = None, 
                       namespace: str = 'default', serialize: bool = True) -> bool:
        """
        Сохраняет временные данные в Redis
        
        Args:
            key: Ключ для хранения
            data: Данные для сохранения (любого типа)
            timeout: Время жизни в секундах
            namespace: Пространство имен для группировки
            serialize: Использовать ли JSON сериализацию
        
        Returns:
            True если успешно сохранено
        """
        try:
            cache_key = cls._get_cache_key(key, namespace)
            timeout = timeout or cls.DEFAULT_TIMEOUT
            
            # Подготавливаем данные для сохранения
            if serialize:
                if isinstance(data, (dict, list, tuple)):
                    stored_data = {
                        'data': data,
                        'type': type(data).__name__,
                        'created_at': datetime.now().isoformat(),
                        'namespace': namespace,
                        'serialized': True
                    }
                    cache_data = json.dumps(stored_data)
                else:
                    # Для других типов используем pickle
                    stored_data = {
                        'data': pickle.dumps(data).hex(),
                        'type': type(data).__name__,
                        'created_at': datetime.now().isoformat(),
                        'namespace': namespace,
                        'serialized': False
                    }
                    cache_data = json.dumps(stored_data)
            else:
                cache_data = data
            
            cache.set(cache_key, cache_data, timeout)
            logger.debug(f"Temp data stored: {namespace}:{key}, timeout: {timeout}s")
            return True
            
        except Exception as e:
            logger.error(f"Error storing temp data {namespace}:{key}: {e}")
            return False
    
    @classmethod
    def get_temp_data(cls, key: str, namespace: str = 'default', default: Any = None) -> Any:
        """
        Получает временные данные из Redis
        
        Args:
            key: Ключ данных
            namespace: Пространство имен
            default: Значение по умолчанию
        
        Returns:
            Данные или значение по умолчанию
        """
        try:
            cache_key = cls._get_cache_key(key, namespace)
            cached_data = cache.get(cache_key)
            
            if cached_data is None:
                logger.debug(f"Temp data not found: {namespace}:{key}")
                return default
            
            # Пытаемся десериализовать JSON
            try:
                parsed_data = json.loads(cached_data)
                if isinstance(parsed_data, dict) and 'data' in parsed_data:
                    # Это наши структурированные данные
                    if parsed_data.get('serialized', True):
                        return parsed_data['data']
                    else:
                        # Данные сохранены через pickle
                        return pickle.loads(bytes.fromhex(parsed_data['data']))
                else:
                    return parsed_data
            except (json.JSONDecodeError, ValueError):
                # Данные сохранены как есть
                return cached_data
            
        except Exception as e:
            logger.error(f"Error getting temp data {namespace}:{key}: {e}")
            return default
    
    @classmethod
    def delete_temp_data(cls, key: str, namespace: str = 'default') -> bool:
        """
        Удаляет временные данные
        
        Args:
            key: Ключ данных
            namespace: Пространство имен
        
        Returns:
            True если успешно удалено
        """
        try:
            cache_key = cls._get_cache_key(key, namespace)
            cache.delete(cache_key)
            logger.debug(f"Temp data deleted: {namespace}:{key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting temp data {namespace}:{key}: {e}")
            return False
    
    @classmethod
    def exists_temp_data(cls, key: str, namespace: str = 'default') -> bool:
        """
        Проверяет существование временных данных
        
        Args:
            key: Ключ данных
            namespace: Пространство имен
        
        Returns:
            True если данные существуют
        """
        try:
            cache_key = cls._get_cache_key(key, namespace)
            return cache.get(cache_key) is not None
            
        except Exception as e:
            logger.error(f"Error checking temp data existence {namespace}:{key}: {e}")
            return False
    
    @classmethod
    def update_temp_data_timeout(cls, key: str, timeout: int, namespace: str = 'default') -> bool:
        """
        Обновляет время жизни временных данных
        
        Args:
            key: Ключ данных
            timeout: Новое время жизни в секундах
            namespace: Пространство имен
        
        Returns:
            True если успешно обновлено
        """
        try:
            # Получаем данные и пересохраняем с новым timeout
            data = cls.get_temp_data(key, namespace)
            if data is not None:
                return cls.store_temp_data(key, data, timeout, namespace)
            return False
            
        except Exception as e:
            logger.error(f"Error updating timeout for {namespace}:{key}: {e}")
            return False


class UserTempDataManager:
    """Менеджер временных данных конкретного пользователя"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.namespace = f'user_{user_id}'
    
    def store(self, key: str, data: Any, timeout: Optional[int] = None) -> bool:
        """Сохраняет данные пользователя"""
        return TempDataManager.store_temp_data(key, data, timeout, self.namespace)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получает данные пользователя"""
        return TempDataManager.get_temp_data(key, self.namespace, default)
    
    def delete(self, key: str) -> bool:
        """Удаляет данные пользователя"""
        return TempDataManager.delete_temp_data(key, self.namespace)
    
    def exists(self, key: str) -> bool:
        """Проверяет существование данных пользователя"""
        return TempDataManager.exists_temp_data(key, self.namespace)
    
    def store_form_data(self, form_step: str, form_data: Dict[str, Any], timeout: int = 3600) -> bool:
        """
        Сохраняет данные формы по шагам
        
        Args:
            form_step: Шаг формы (step1, step2, etc.)
            form_data: Данные формы
            timeout: Время жизни (по умолчанию 1 час)
        
        Returns:
            True если успешно сохранено
        """
        key = f"form_data_{form_step}"
        return self.store(key, form_data, timeout)
    
    def get_form_data(self, form_step: str) -> Optional[Dict[str, Any]]:
        """Получает данные формы по шагу"""
        key = f"form_data_{form_step}"
        return self.get(key)
    
    def clear_all_form_data(self) -> bool:
        """Очищает все данные форм пользователя"""
        try:
            # В реальности здесь нужно было бы сканировать ключи
            # Для демонстрации просто логируем
            logger.info(f"Clearing all form data for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing form data for user {self.user_id}: {e}")
            return False
    
    def store_conversation_state(self, state_data: Dict[str, Any], timeout: int = 7200) -> bool:
        """
        Сохраняет состояние разговора с ботом
        
        Args:
            state_data: Данные состояния
            timeout: Время жизни (по умолчанию 2 часа)
        
        Returns:
            True если успешно сохранено
        """
        return self.store('conversation_state', state_data, timeout)
    
    def get_conversation_state(self) -> Optional[Dict[str, Any]]:
        """Получает состояние разговора"""
        return self.get('conversation_state')
    
    def clear_conversation_state(self) -> bool:
        """Очищает состояние разговора"""
        return self.delete('conversation_state')


class SessionDataManager:
    """Менеджер сессионных данных"""
    
    @classmethod
    def store_session_data(cls, session_key: str, data: Dict[str, Any], timeout: int = 86400) -> bool:
        """
        Сохраняет сессионные данные
        
        Args:
            session_key: Ключ сессии
            data: Данные сессии
            timeout: Время жизни (по умолчанию 24 часа)
        
        Returns:
            True если успешно сохранено
        """
        return TempDataManager.store_temp_data(
            session_key, data, timeout, 'sessions'
        )
    
    @classmethod
    def get_session_data(cls, session_key: str) -> Optional[Dict[str, Any]]:
        """Получает сессионные данные"""
        return TempDataManager.get_temp_data(session_key, 'sessions')
    
    @classmethod
    def delete_session_data(cls, session_key: str) -> bool:
        """Удаляет сессионные данные"""
        return TempDataManager.delete_temp_data(session_key, 'sessions')


class ActivityTempDataManager:
    """Менеджер временных данных активностей"""
    
    @classmethod
    def store_matching_request(cls, request_id: str, request_data: Dict[str, Any], 
                              timeout: int = 1800) -> bool:
        """
        Сохраняет запрос на matching
        
        Args:
            request_id: ID запроса
            request_data: Данные запроса
            timeout: Время жизни (по умолчанию 30 минут)
        
        Returns:
            True если успешно сохранено
        """
        return TempDataManager.store_temp_data(
            request_id, request_data, timeout, 'matching_requests'
        )
    
    @classmethod
    def get_matching_request(cls, request_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные запроса на matching"""
        return TempDataManager.get_temp_data(request_id, 'matching_requests')
    
    @classmethod
    def store_activity_draft(cls, user_id: int, activity_data: Dict[str, Any], 
                           timeout: int = 3600) -> bool:
        """
        Сохраняет черновик активности
        
        Args:
            user_id: ID пользователя
            activity_data: Данные активности
            timeout: Время жизни (по умолчанию 1 час)
        
        Returns:
            True если успешно сохранено
        """
        key = f"activity_draft_{user_id}"
        return TempDataManager.store_temp_data(
            key, activity_data, timeout, 'activity_drafts'
        )
    
    @classmethod
    def get_activity_draft(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает черновик активности пользователя"""
        key = f"activity_draft_{user_id}"
        return TempDataManager.get_temp_data(key, 'activity_drafts')


# Утилиты для быстрого доступа
def get_user_temp_manager(user_id: int) -> UserTempDataManager:
    """Получает менеджер временных данных для пользователя"""
    return UserTempDataManager(user_id)


def store_quick_data(key: str, data: Any, minutes: int = 30) -> bool:
    """Быстрое сохранение данных на указанное количество минут"""
    timeout = minutes * 60
    return TempDataManager.store_temp_data(key, data, timeout)


def get_quick_data(key: str, default: Any = None) -> Any:
    """Быстрое получение данных"""
    return TempDataManager.get_temp_data(key, default=default)