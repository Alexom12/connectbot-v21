"""
Django management команда для работы с Redis кешем
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from employees.redis_utils import RedisManager
from employees.models import Employee, Activity


class Command(BaseCommand):
    help = 'Управление Redis кешем для ConnectBot v21'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['status', 'clear', 'warmup', 'test'],
            help='Действие: status - статус Redis, clear - очистить кеш, warmup - прогрев кеша, test - тестирование'
        )
        parser.add_argument(
            '--employee-id',
            type=int,
            help='ID сотрудника для операций с конкретным пользователем'
        )
        parser.add_argument(
            '--activity-id',
            type=int,
            help='ID активности для операций с конкретной активностью'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self.show_redis_status()
        elif action == 'clear':
            self.clear_cache(options.get('employee_id'), options.get('activity_id'))
        elif action == 'warmup':
            self.warmup_cache()
        elif action == 'test':
            self.test_redis()
    
    def show_redis_status(self):
        """Показать статус Redis и статистику кеша"""
        self.stdout.write(self.style.HTTP_INFO('🔍 Проверка статуса Redis...'))
        
        if RedisManager.is_redis_available():
            self.stdout.write(self.style.SUCCESS('✅ Redis доступен'))
            
            # Попробуем получить некоторую статистику
            try:
                # Тестовые операции
                cache.set('test_key', 'test_value', 10)
                result = cache.get('test_key')
                cache.delete('test_key')
                
                if result == 'test_value':
                    self.stdout.write(self.style.SUCCESS('✅ Запись/чтение в Redis работает'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Проблемы с записью/чтением Redis'))
                
                # Покажем информацию о кешированных данных
                self.stdout.write('\n📊 Статистика кешированных данных:')
                
                # Проверим несколько ключей сотрудников
                employees_cached = 0
                total_employees = Employee.objects.filter(is_active=True).count()
                
                for emp in Employee.objects.filter(is_active=True, telegram_id__isnull=False)[:10]:
                    if RedisManager.get_employee_data(emp.telegram_id):
                        employees_cached += 1
                
                self.stdout.write(f'   Сотрудники в кеше: {employees_cached}/{min(total_employees, 10)} (выборочно)')
                
                # Проверим активности
                activities_cached = 0
                total_activities = Activity.objects.filter(status__in=['scheduled', 'active']).count()
                
                for act in Activity.objects.filter(status__in=['scheduled', 'active'])[:10]:
                    if RedisManager.get_activity_participants(act.id):
                        activities_cached += 1
                
                self.stdout.write(f'   Активности в кеше: {activities_cached}/{min(total_activities, 10)} (выборочно)')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка при работе с Redis: {e}'))
        else:
            self.stdout.write(self.style.ERROR('❌ Redis недоступен'))
            self.stdout.write('Проверьте:')
            self.stdout.write('  - Запущен ли Redis сервер: docker-compose up -d')
            self.stdout.write('  - Правильные ли настройки в .env файле')
    
    def clear_cache(self, employee_id=None, activity_id=None):
        """Очистить кеш"""
        if employee_id:
            # Очистить кеш конкретного сотрудника
            try:
                employee = Employee.objects.get(id=employee_id)
                if employee.telegram_id:
                    success = RedisManager.invalidate_employee_cache(employee.telegram_id)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Кеш сотрудника {employee.full_name} очищен')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Не удалось очистить кеш сотрудника {employee.full_name}')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  У сотрудника {employee.full_name} нет Telegram ID')
                    )
            except Employee.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Сотрудник с ID {employee_id} не найден'))
        
        elif activity_id:
            # Очистить кеш конкретной активности
            try:
                activity = Activity.objects.get(id=activity_id)
                key = f"{RedisManager.PREFIX_ACTIVITY}{activity_id}:participants"
                cache.delete(key)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Кеш активности "{activity.title}" очищен')
                )
            except Activity.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Активность с ID {activity_id} не найдена'))
        
        else:
            # Очистить весь кеш
            try:
                cache.clear()
                self.stdout.write(self.style.SUCCESS('✅ Весь кеш очищен'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка при очистке кеша: {e}'))
    
    def warmup_cache(self):
        """Прогрев кеша популярными данными"""
        self.stdout.write(self.style.HTTP_INFO('🔥 Прогрев кеша...'))
        
        # Кешируем данные активных сотрудников с Telegram ID
        employees_cached = 0
        for employee in Employee.objects.filter(is_active=True, telegram_id__isnull=False):
            data = {
                'id': employee.id,
                'full_name': employee.full_name,
                'position': employee.position,
                'telegram_id': employee.telegram_id,
                'telegram_username': employee.telegram_username,
            }
            if RedisManager.cache_employee_data(employee.telegram_id, data):
                employees_cached += 1
            
            # Кешируем интересы сотрудника
            interests = employee.get_interests_list()  # Это уже использует кеширование
        
        self.stdout.write(self.style.SUCCESS(f'✅ Закешированы данные {employees_cached} сотрудников'))
        
        # Кешируем участников активных активностей
        activities_cached = 0
        for activity in Activity.objects.filter(status__in=['scheduled', 'active']):
            activity.get_participants_count()  # Это уже использует кеширование
            activities_cached += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Закешированы данные {activities_cached} активностей'))
        
        self.stdout.write(self.style.SUCCESS('🎉 Прогрев кеша завершен!'))
    
    def test_redis(self):
        """Тестирование функций Redis"""
        self.stdout.write(self.style.HTTP_INFO('🧪 Тестирование Redis функций...'))
        
        # Тест 1: Базовые операции
        self.stdout.write('Тест 1: Базовые операции кеша')
        try:
            cache.set('test_key', {'test': 'data'}, 10)
            result = cache.get('test_key')
            cache.delete('test_key')
            
            if result and result.get('test') == 'data':
                self.stdout.write(self.style.SUCCESS('  ✅ Базовые операции работают'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ Проблемы с базовыми операциями'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка базовых операций: {e}'))
            return
        
        # Тест 2: Функции RedisManager
        self.stdout.write('\nТест 2: Функции RedisManager')
        
        # Тестовые данные сотрудника
        test_employee_data = {
            'id': 999,
            'full_name': 'Тестовый Пользователь',
            'position': 'Тестер',
            'telegram_id': 123456789,
            'telegram_username': 'testuser',
        }
        
        try:
            # Кеширование данных сотрудника
            success = RedisManager.cache_employee_data(123456789, test_employee_data)
            if success:
                self.stdout.write('  ✅ Кеширование данных сотрудника работает')
            else:
                self.stdout.write('  ❌ Проблемы с кешированием данных сотрудника')
            
            # Получение данных сотрудника
            cached_data = RedisManager.get_employee_data(123456789)
            if cached_data and cached_data.get('full_name') == 'Тестовый Пользователь':
                self.stdout.write('  ✅ Получение данных сотрудника работает')
            else:
                self.stdout.write('  ❌ Проблемы с получением данных сотрудника')
            
            # Очистка тестовых данных
            RedisManager.invalidate_employee_cache(123456789)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка функций RedisManager: {e}'))
        
        # Тест 3: Сессии бота
        self.stdout.write('\nТест 3: Сессии бота')
        try:
            test_session = {'current_menu': 'main', 'user_state': 'active'}
            
            # Сохранение сессии
            success = RedisManager.store_bot_session(123456789, test_session)
            if success:
                self.stdout.write('  ✅ Сохранение сессии работает')
            else:
                self.stdout.write('  ❌ Проблемы с сохранением сессии')
            
            # Получение сессии
            session_data = RedisManager.get_bot_session(123456789)
            if session_data and session_data.get('current_menu') == 'main':
                self.stdout.write('  ✅ Получение сессии работает')
            else:
                self.stdout.write('  ❌ Проблемы с получением сессии')
            
            # Очистка сессии
            RedisManager.clear_bot_session(123456789)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка сессий бота: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Тестирование завершено!'))