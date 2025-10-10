"""
Event Publishing система для микросервисов через Redis
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from django.core.cache import cache
from django.conf import settings
import redis
from redis import Redis

logger = logging.getLogger(__name__)


class EventPublisher:
    """Система публикации событий через Redis"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.channel_prefix = 'connectbot'
    
    def _get_redis_client(self) -> Redis:
        """Получает клиент Redis для pub/sub"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, decode_responses=True)
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def publish_event(self, event_type: str, data: Dict[str, Any], 
                     channel: Optional[str] = None, user_id: Optional[int] = None) -> bool:
        """
        Публикует событие в Redis channel
        
        Args:
            event_type: Тип события (user.created, activity.scheduled, etc.)
            data: Данные события
            channel: Канал для публикации (если не указан, генерируется автоматически)
            user_id: ID пользователя для персональных событий
        
        Returns:
            True если событие успешно опубликовано
        """
        try:
            # Формируем канал
            if not channel:
                if user_id:
                    channel = f"{self.channel_prefix}:user:{user_id}"
                else:
                    channel = f"{self.channel_prefix}:global"
            
            # Создаем структуру события
            event = {
                'id': str(uuid.uuid4()),
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'channel': channel,
                'user_id': user_id,
                'source': 'django-connectbot'
            }
            
            # Публикуем событие
            subscribers = self.redis_client.publish(channel, json.dumps(event))
            
            logger.info(f"Event {event_type} published to {channel}, subscribers: {subscribers}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            return False
    
    def publish_user_event(self, user_id: int, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Публикует персональное событие пользователя
        
        Args:
            user_id: ID пользователя
            event_type: Тип события
            data: Данные события
        
        Returns:
            True если успешно опубликовано
        """
        return self.publish_event(event_type, data, user_id=user_id)
    
    def publish_global_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Публикует глобальное событие для всех подписчиков
        
        Args:
            event_type: Тип события
            data: Данные события
        
        Returns:
            True если успешно опубликовано
        """
        return self.publish_event(event_type, data, channel=f"{self.channel_prefix}:global")
    
    def publish_microservice_event(self, service_name: str, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Публикует событие для конкретного микросервиса
        
        Args:
            service_name: Имя микросервиса (matching, notifications, etc.)
            event_type: Тип события
            data: Данные события
        
        Returns:
            True если успешно опубликовано
        """
        channel = f"{self.channel_prefix}:service:{service_name}"
        return self.publish_event(event_type, data, channel=channel)


class EventSubscriber:
    """Система подписки на события через Redis"""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.channel_prefix = 'connectbot'
        self.handlers: Dict[str, List[Callable]] = {}
        self.pubsub = None
    
    def _get_redis_client(self) -> Redis:
        """Получает клиент Redis для pub/sub"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, decode_responses=True)
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def subscribe_to_channel(self, channel: str) -> bool:
        """
        Подписывается на канал событий
        
        Args:
            channel: Имя канала
        
        Returns:
            True если успешно подписались
        """
        try:
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()
            
            self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            return False
    
    def subscribe_to_user_events(self, user_id: int) -> bool:
        """Подписывается на события пользователя"""
        channel = f"{self.channel_prefix}:user:{user_id}"
        return self.subscribe_to_channel(channel)
    
    def subscribe_to_global_events(self) -> bool:
        """Подписывается на глобальные события"""
        channel = f"{self.channel_prefix}:global"
        return self.subscribe_to_channel(channel)
    
    def subscribe_to_service_events(self, service_name: str) -> bool:
        """Подписывается на события микросервиса"""
        channel = f"{self.channel_prefix}:service:{service_name}"
        return self.subscribe_to_channel(channel)
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Регистрирует обработчик для типа события
        
        Args:
            event_type: Тип события
            handler: Функция-обработчик
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def listen_for_messages(self, timeout: int = 1) -> None:
        """
        Слушает сообщения из подписанных каналов
        
        Args:
            timeout: Таймаут в секундах
        """
        if not self.pubsub:
            logger.warning("Not subscribed to any channels")
            return
        
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    self._handle_message(message)
                    
        except KeyboardInterrupt:
            logger.info("Stopping event listener")
            self.pubsub.close()
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Обрабатывает полученное сообщение"""
        try:
            event = json.loads(message['data'])
            event_type = event.get('type')
            
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in handler for {event_type}: {e}")
            else:
                logger.debug(f"No handler for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")


class ConnectBotEvents:
    """Предопределенные типы событий ConnectBot"""
    
    # Пользовательские события
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    USER_LOGIN = 'user.login'
    USER_LOGOUT = 'user.logout'
    
    # События активностей
    ACTIVITY_CREATED = 'activity.created'
    ACTIVITY_UPDATED = 'activity.updated'
    ACTIVITY_CANCELLED = 'activity.cancelled'
    ACTIVITY_COMPLETED = 'activity.completed'
    
    # События matching
    MATCHING_REQUEST = 'matching.request'
    MATCHING_COMPLETED = 'matching.completed'
    MATCHING_FAILED = 'matching.failed'
    
    # Системные события
    CACHE_CLEARED = 'system.cache_cleared'
    SERVICE_STARTED = 'system.service_started'
    SERVICE_STOPPED = 'system.service_stopped'
    
    # Уведомления
    NOTIFICATION_SENT = 'notification.sent'
    NOTIFICATION_DELIVERED = 'notification.delivered'
    NOTIFICATION_READ = 'notification.read'


# Глобальный экземпляр издателя
event_publisher = EventPublisher()


def publish_user_created(user_data: Dict[str, Any]) -> bool:
    """Утилита для публикации события создания пользователя"""
    return event_publisher.publish_global_event(
        ConnectBotEvents.USER_CREATED, 
        {'user': user_data}
    )


def publish_activity_scheduled(activity_id: int, user_id: int, activity_data: Dict[str, Any]) -> bool:
    """Утилита для публикации события планирования активности"""
    return event_publisher.publish_user_event(
        user_id,
        ConnectBotEvents.ACTIVITY_CREATED,
        {'activity_id': activity_id, 'activity': activity_data}
    )


def publish_matching_request(users: List[int], matching_type: str = 'coffee') -> bool:
    """Утилита для публикации запроса на matching"""
    return event_publisher.publish_microservice_event(
        'matching',
        ConnectBotEvents.MATCHING_REQUEST,
        {'users': users, 'type': matching_type}
    )


def publish_cache_cleared(cache_type: str, user_id: Optional[int] = None) -> bool:
    """Утилита для публикации события очистки кэша"""
    data = {'cache_type': cache_type}
    if user_id:
        data['user_id'] = user_id
        return event_publisher.publish_user_event(user_id, ConnectBotEvents.CACHE_CLEARED, data)
    else:
        return event_publisher.publish_global_event(ConnectBotEvents.CACHE_CLEARED, data)