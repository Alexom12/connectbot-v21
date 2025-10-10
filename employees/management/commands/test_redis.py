"""
Management команда для тестирования Redis интеграции
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from employees.redis_integration import redis_integration
from employees.redis_utils import EnhancedRedisManager
from employees.redis_events import ConnectBotEvents


class Command(BaseCommand):
    help = 'Тестирует Redis интеграцию ConnectBot'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--component',
            choices=['all', 'cache', 'events', 'temp_data', 'health'],
            default='all',
            help='Компонент для тестирования'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=123,
            help='ID пользователя для тестов'
        )
    
    def handle(self, *args, **options):
        component = options['component']
        user_id = options['user_id']
        
        self.stdout.write(
            self.style.SUCCESS(f'🧪 Тестирование Redis интеграции ConnectBot')
        )
        self.stdout.write(f'Компонент: {component}, Пользователь: {user_id}')
        self.stdout.write('-' * 50)
        
        if component in ['all', 'health']:
            self.test_health()
        
        if component in ['all', 'cache']:
            self.test_cache(user_id)
        
        if component in ['all', 'events']:
            self.test_events(user_id)
        
        if component in ['all', 'temp_data']:
            self.test_temp_data(user_id)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Тестирование завершено!')
        )
    
    def test_health(self):
        """Тестирует здоровье Redis"""
        self.stdout.write(self.style.WARNING('📊 Тестирование здоровья Redis...'))
        
        try:
            health_info = redis_integration.health_check()
            
            self.stdout.write(f"Статус: {health_info.get('status', 'unknown')}")
            self.stdout.write(f"Redis доступен: {health_info.get('redis_available', False)}")
            self.stdout.write(f"Backend: {health_info.get('cache_backend', 'unknown')}")
            self.stdout.write(f"Redis URL: {health_info.get('redis_url', 'не настроен')}")
            self.stdout.write(f"Java Service URL: {health_info.get('java_service_url', 'не настроен')}")
            
            if health_info.get('redis_available'):
                self.stdout.write(self.style.SUCCESS('✅ Redis работает нормально'))
            else:
                self.stdout.write(self.style.ERROR('❌ Redis недоступен'))
                if 'error' in health_info:
                    self.stdout.write(f"Ошибка: {health_info['error']}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка тестирования здоровья: {e}'))
        
        self.stdout.write('')
    
    def test_cache(self, user_id):
        """Тестирует кэширование меню"""
        self.stdout.write(self.style.WARNING('🗂️ Тестирование кэширования меню...'))
        
        try:
            # Создаем тестовые данные меню
            test_menu = {
                'type': 'main',
                'user_id': user_id,
                'options': [
                    {'key': 'profile', 'label': '👤 Профиль'},
                    {'key': 'activities', 'label': '🎯 Активности'},
                    {'key': 'settings', 'label': '⚙️ Настройки'},
                ]
            }
            
            # Тест сохранения
            success = redis_integration.menu_cache.set_user_menu(user_id, test_menu)
            if success:
                self.stdout.write('✅ Меню сохранено в кэш')
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка сохранения меню'))
            
            # Тест получения
            cached_menu = redis_integration.menu_cache.get_user_menu(user_id)
            if cached_menu:
                self.stdout.write('✅ Меню получено из кэша')
                self.stdout.write(f"Опций в меню: {len(cached_menu.get('data', {}).get('options', []))}")
            else:
                self.stdout.write(self.style.ERROR('❌ Меню не найдено в кэше'))
            
            # Тест построителя меню
            built_menu = redis_integration.menu_builder.build_main_menu(user_id, 'admin')
            if built_menu:
                self.stdout.write('✅ Меню построено через MenuBuilder')
                self.stdout.write(f"Роль пользователя: {built_menu.get('role')}")
            
            # Тест очистки
            success = redis_integration.menu_cache.delete_user_menu(user_id)
            if success:
                self.stdout.write('✅ Меню удалено из кэша')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка тестирования кэша: {e}'))
        
        self.stdout.write('')
    
    def test_events(self, user_id):
        """Тестирует систему событий"""
        self.stdout.write(self.style.WARNING('📡 Тестирование системы событий...'))
        
        try:
            # Тест публикации пользовательского события
            success = redis_integration.events.publish_user_event(
                user_id,
                ConnectBotEvents.USER_LOGIN,
                {'timestamp': timezone.now().isoformat(), 'source': 'test_command'}
            )
            if success:
                self.stdout.write('✅ Пользовательское событие опубликовано')
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка публикации пользовательского события'))
            
            # Тест публикации глобального события
            success = redis_integration.events.publish_global_event(
                ConnectBotEvents.SERVICE_STARTED,
                {'service': 'test_service', 'timestamp': timezone.now().isoformat()}
            )
            if success:
                self.stdout.write('✅ Глобальное событие опубликовано')
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка публикации глобального события'))
            
            # Тест публикации события микросервиса
            success = redis_integration.events.publish_microservice_event(
                'matching',
                ConnectBotEvents.MATCHING_REQUEST,
                {'users': [user_id, user_id + 1], 'type': 'coffee'}
            )
            if success:
                self.stdout.write('✅ Событие микросервиса опубликовано')
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка публикации события микросервиса'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка тестирования событий: {e}'))
        
        self.stdout.write('')
    
    def test_temp_data(self, user_id):
        """Тестирует временные данные"""
        self.stdout.write(self.style.WARNING('🗄️ Тестирование временных данных...'))
        
        try:
            # Получаем менеджер пользователя
            user_manager = redis_integration.get_user_manager(user_id)
            
            # Тест сохранения данных формы
            form_data = {
                'step': 1,
                'preferences': ['coffee', 'lunch'],
                'notification_time': '10:00'
            }
            success = user_manager.store_form_data('preferences_step1', form_data)
            if success:
                self.stdout.write('✅ Данные формы сохранены')
            
            # Тест получения данных формы
            retrieved_data = user_manager.get_form_data('preferences_step1')
            if retrieved_data:
                self.stdout.write('✅ Данные формы получены')
                self.stdout.write(f"Шаг формы: {retrieved_data.get('step')}")
            
            # Тест состояния разговора
            conversation_state = {
                'current_menu': 'main',
                'last_action': 'show_profile',
                'context': {'editing_preferences': True}
            }
            success = user_manager.store_conversation_state(conversation_state)
            if success:
                self.stdout.write('✅ Состояние разговора сохранено')
            
            # Тест получения состояния разговора
            retrieved_state = user_manager.get_conversation_state()
            if retrieved_state:
                self.stdout.write('✅ Состояние разговора получено')
                self.stdout.write(f"Текущее меню: {retrieved_state.get('current_menu')}")
            
            # Тест общих временных данных
            test_data = {'test_key': 'test_value', 'number': 42}
            success = redis_integration.temp_data.store_temp_data(
                'test_key', test_data, 300, 'test_namespace'
            )
            if success:
                self.stdout.write('✅ Общие временные данные сохранены')
            
            retrieved_test_data = redis_integration.temp_data.get_temp_data(
                'test_key', 'test_namespace'
            )
            if retrieved_test_data:
                self.stdout.write('✅ Общие временные данные получены')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка тестирования временных данных: {e}'))
        
        self.stdout.write('')