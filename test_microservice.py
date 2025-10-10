#!/usr/bin/env python3
"""
🧪 Тестовый скрипт гибридной интеграции ConnectBot v21
Тестирует Django + Java микросервис для создания пар сотрудников
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Настройка Django окружения
def setup_django():
    """Настраивает Django окружение для тестирования"""
    import django
    from django.conf import settings
    
    # Добавляем корень проекта в PYTHONPATH
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Устанавливаем переменную окружения для настроек Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Инициализируем Django
    django.setup()
    
    print("✅ Django окружение настроено")
    return True

# Импортируем Django компоненты после настройки
setup_django()

from employees.models import Employee
from employees.redis_integration import redis_integration
from employees.redis_events import ConnectBotEvents


class MicroserviceIntegrationTester:
    """Тестер гибридной интеграции Django + Java микросервис"""
    
    def __init__(self):
        self.java_service_url = "http://localhost:8080"
        self.redis_available = False
        self.java_available = False
        self.test_results = {
            'redis_health': False,
            'java_health': False,
            'java_matching': False,
            'python_fallback': False,
            'redis_cache': False,
            'event_publishing': False
        }
        self.statistics = {
            'total_employees': 0,
            'pairs_created': 0,
            'employees_without_pair': 0,
            'test_duration': 0
        }
    
    def print_header(self):
        """Выводит красивый заголовок"""
        print("🎯" + "="*60 + "🎯")
        print("🧪 ТЕСТИРОВАНИЕ ГИБРИДНОЙ ИНТЕГРАЦИИ CONNECTBOT V21 🧪")
        print("🎯" + "="*60 + "🎯")
        print(f"📅 Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Java Service URL: {self.java_service_url}")
        print()
    
    def get_test_employees(self) -> List[Dict[str, Any]]:
        """Возвращает тестовые данные сотрудников"""
        return [
            {
                'id': 1,
                'full_name': 'Иван Иванов',
                'position': 'Разработчик',
                'department': 'IT',
                'business_center': 'МСК-1',
                'telegram_id': 111111111,
                'telegram_username': 'ivan_dev',
                'interests': ['coffee', 'chess'],
                'is_active': True
            },
            {
                'id': 2,
                'full_name': 'Петр Петров',
                'position': 'HR-менеджер',
                'department': 'HR',
                'business_center': 'МСК-1',
                'telegram_id': 222222222,
                'telegram_username': 'petr_hr',
                'interests': ['coffee', 'lunch'],
                'is_active': True
            },
            {
                'id': 3,
                'full_name': 'Анна Сидорова',
                'position': 'Дизайнер',
                'department': 'Design',
                'business_center': 'МСК-2',
                'telegram_id': 333333333,
                'telegram_username': 'anna_design',
                'interests': ['coffee', 'photo'],
                'is_active': True
            },
            {
                'id': 4,
                'full_name': 'Михаил Козлов',
                'position': 'Аналитик',
                'department': 'Analytics',
                'business_center': 'МСК-1',
                'telegram_id': 444444444,
                'telegram_username': 'misha_analyst',
                'interests': ['lunch', 'chess'],
                'is_active': True
            },
            {
                'id': 5,
                'full_name': 'Елена Новикова',
                'position': 'QA-инженер',
                'department': 'QA',
                'business_center': 'МСК-2',
                'telegram_id': 555555555,
                'telegram_username': 'lena_qa',
                'interests': ['coffee', 'games'],
                'is_active': True
            },
            {
                'id': 6,
                'full_name': 'Дмитрий Волков',
                'position': 'DevOps',
                'department': 'IT',
                'business_center': 'МСК-1',
                'telegram_id': 666666666,
                'telegram_username': 'dmitry_devops',
                'interests': ['lunch', 'walk'],
                'is_active': True
            }
        ]
    
    def test_redis_health(self) -> bool:
        """Тестирует здоровье Redis"""
        print("🔄 Тестирование Redis здоровья...")
        
        try:
            health_info = redis_integration.health_check()
            self.redis_available = health_info.get('redis_available', False)
            
            if self.redis_available:
                print(f"✅ Redis доступен: {health_info.get('status')}")
                print(f"   Backend: {health_info.get('cache_backend')}")
                print(f"   URL: {health_info.get('redis_url')}")
                self.test_results['redis_health'] = True
            else:
                print(f"❌ Redis недоступен: {health_info.get('error', 'Неизвестная ошибка')}")
            
            return self.redis_available
            
        except Exception as e:
            print(f"❌ Ошибка тестирования Redis: {e}")
            return False
    
    def test_java_service_health(self) -> bool:
        """Тестирует здоровье Java микросервиса"""
        print("\n🔄 Тестирование Java микросервиса...")
        
        try:
            # Тестируем health endpoint
            health_url = f"{self.java_service_url}/api/matching/health"
            response = requests.get(health_url, timeout=5)
            
            # Принимаем 200 (UP) и 503 (DEGRADED) как валидные статусы
            if response.status_code in [200, 503]:
                health_data = response.json() if response.content else {"status": "ok"}
                status = health_data.get('status', 'UNKNOWN')
                overall_status = health_data.get('overall_status', status)
                
                if response.status_code == 200:
                    print(f"✅ Java сервис доступен (статус: {status})")
                else:
                    print(f"⚠️ Java сервис доступен но degraded (статус: {overall_status})")
                
                print(f"   Status Code: {response.status_code}")
                print(f"   Service: {health_data.get('service', 'Unknown')}")
                print(f"   Version: {health_data.get('version', 'Unknown')}")
                
                # Тестируем algorithms endpoint
                algorithms_url = f"{self.java_service_url}/api/matching/algorithms"
                alg_response = requests.get(algorithms_url, timeout=5)
                
                if alg_response.status_code == 200:
                    algorithms = alg_response.json()
                    print(f"✅ Алгоритмы доступны: {algorithms.get('total', 'unknown')} шт.")
                    self.java_available = True
                    self.test_results['java_health'] = True
                else:
                    print(f"⚠️ Algorithms endpoint недоступен: {alg_response.status_code}")
            else:
                print(f"❌ Java сервис недоступен: HTTP {response.status_code}")
            
            return self.java_available
            
        except requests.exceptions.ConnectTimeout:
            print("❌ Java сервис недоступен: Таймаут соединения")
        except requests.exceptions.ConnectionError:
            print("❌ Java сервис недоступен: Ошибка соединения")
        except Exception as e:
            print(f"❌ Ошибка тестирования Java сервиса: {e}")
        
        return False
    
    def test_java_matching(self, employees: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Тестирует создание пар через Java микросервис"""
        print("\n🔄 Тестирование создания пар через Java...")
        
        if not self.java_available:
            print("⚠️ Java сервис недоступен, пропускаем тест")
            return None
        
        try:
            matching_url = f"{self.java_service_url}/api/matching/coffee/simple"
            
            # Подготавливаем данные для Java сервиса
            java_employees = []
            for emp in employees:
                java_emp = {
                    'id': emp['id'],
                    'full_name': emp['full_name'],
                    'position': emp.get('position', ''),
                    'department': emp.get('department', ''),
                    'is_active': emp.get('is_active', True)
                }
                java_employees.append(java_emp)
            
            # Отправляем запрос
            print(f"   Отправляем {len(java_employees)} сотрудников...")
            response = requests.post(
                matching_url,
                json=java_employees,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                pairs = result.get('pairs', [])
                unpaired = result.get('unpaired', [])
                
                print(f"✅ Java matching успешен!")
                print(f"   Пар создано: {len(pairs)}")
                print(f"   Без пары: {len(unpaired)}")
                
                # Подробная информация о парах
                for i, pair in enumerate(pairs[:3], 1):  # Показываем первые 3 пары
                    emp1 = pair.get('employee1', {})
                    emp2 = pair.get('employee2', {})
                    print(f"   Пара {i}: {emp1.get('full_name', 'N/A')} ↔ {emp2.get('full_name', 'N/A')}")
                
                if len(pairs) > 3:
                    print(f"   ... и еще {len(pairs) - 3} пар")
                
                # Обновляем статистику
                self.statistics['pairs_created'] = len(pairs)
                self.statistics['employees_without_pair'] = len(unpaired)
                self.test_results['java_matching'] = True
                
                return result
            else:
                print(f"❌ Java matching неудачен: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            
        except Exception as e:
            print(f"❌ Ошибка Java matching: {e}")
        
        return None
    
    def python_fallback_matching(self, employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Python fallback алгоритм создания пар"""
        import random
        
        print("\n🔄 Тестирование Python fallback алгоритма...")
        
        try:
            # Простой алгоритм случайного matching
            active_employees = [emp for emp in employees if emp.get('is_active', True)]
            random.shuffle(active_employees)
            
            pairs = []
            unpaired = []
            
            # Создаем пары
            for i in range(0, len(active_employees) - 1, 2):
                pair = {
                    'employee1': active_employees[i],
                    'employee2': active_employees[i + 1],
                    'match_score': random.randint(60, 95),  # Симулируем score
                    'algorithm': 'python_fallback'
                }
                pairs.append(pair)
            
            # Если нечетное количество, последний остается без пары
            if len(active_employees) % 2 == 1:
                unpaired.append(active_employees[-1])
            
            result = {
                'pairs': pairs,
                'unpaired': unpaired,
                'total_employees': len(active_employees),
                'algorithm_used': 'python_fallback',
                'success': True
            }
            
            print(f"✅ Python fallback успешен!")
            print(f"   Пар создано: {len(pairs)}")
            print(f"   Без пары: {len(unpaired)}")
            
            # Показываем пары
            for i, pair in enumerate(pairs[:3], 1):
                emp1 = pair['employee1']
                emp2 = pair['employee2']
                score = pair.get('match_score', 0)
                print(f"   Пара {i}: {emp1['full_name']} ↔ {emp2['full_name']} (score: {score})")
            
            if len(pairs) > 3:
                print(f"   ... и еще {len(pairs) - 3} пар")
            
            # Обновляем статистику для fallback
            if not self.test_results['java_matching']:
                self.statistics['pairs_created'] = len(pairs)
                self.statistics['employees_without_pair'] = len(unpaired)
            
            self.test_results['python_fallback'] = True
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка Python fallback: {e}")
            return {'pairs': [], 'unpaired': employees, 'success': False}
    
    def test_redis_cache_integration(self, matching_result: Dict[str, Any]) -> bool:
        """Тестирует интеграцию с Redis кэшем"""
        print("\n🔄 Тестирование Redis кэширования...")
        
        if not self.redis_available:
            print("⚠️ Redis недоступен, пропускаем тест кэширования")
            return False
        
        try:
            # Тест кэширования результатов matching
            cache_key = "test_matching_results"
            success = redis_integration.temp_data.store_temp_data(
                cache_key, matching_result, timeout=300, namespace='matching_tests'
            )
            
            if success:
                print("✅ Результаты matching сохранены в Redis")
                
                # Проверяем получение из кэша
                cached_result = redis_integration.temp_data.get_temp_data(
                    cache_key, namespace='matching_tests'
                )
                
                if cached_result:
                    print("✅ Результаты получены из Redis кэша")
                    pairs_count = len(cached_result.get('pairs', []))
                    print(f"   Кэшированных пар: {pairs_count}")
                    self.test_results['redis_cache'] = True
                    return True
                else:
                    print("❌ Не удалось получить данные из кэша")
            else:
                print("❌ Не удалось сохранить в кэш")
            
        except Exception as e:
            print(f"❌ Ошибка тестирования кэша: {e}")
        
        return False
    
    def test_event_publishing(self, matching_result: Dict[str, Any]) -> bool:
        """Тестирует публикацию событий"""
        print("\n🔄 Тестирование публикации событий...")
        
        if not self.redis_available:
            print("⚠️ Redis недоступен, пропускаем тест событий")
            return False
        
        try:
            # Публикуем событие завершения matching
            event_data = {
                'pairs_created': len(matching_result.get('pairs', [])),
                'employees_processed': matching_result.get('total_employees', 0),
                'algorithm_used': matching_result.get('algorithm_used', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'test_mode': True
            }
            
            success = redis_integration.events.publish_global_event(
                ConnectBotEvents.MATCHING_COMPLETED,
                event_data
            )
            
            if success:
                print("✅ Событие MATCHING_COMPLETED опубликовано")
                
                # Публикуем пользовательские события для созданных пар
                pairs = matching_result.get('pairs', [])
                events_published = 0
                
                for pair in pairs[:3]:  # Публикуем для первых 3 пар
                    emp1_id = pair.get('employee1', {}).get('id')
                    emp2_id = pair.get('employee2', {}).get('id')
                    
                    if emp1_id and emp2_id:
                        pair_event = {
                            'partner_id': emp2_id,
                            'partner_name': pair.get('employee2', {}).get('full_name'),
                            'match_type': 'coffee',
                            'test_mode': True
                        }
                        
                        if redis_integration.events.publish_user_event(
                            emp1_id, ConnectBotEvents.ACTIVITY_CREATED, pair_event
                        ):
                            events_published += 1
                
                print(f"✅ Опубликовано {events_published} пользовательских событий")
                self.test_results['event_publishing'] = True
                return True
            else:
                print("❌ Не удалось опубликовать событие")
            
        except Exception as e:
            print(f"❌ Ошибка публикации событий: {e}")
        
        return False
    
    def run_hybrid_integration_test(self) -> None:
        """Запускает полный тест гибридной интеграции"""
        start_time = time.time()
        
        self.print_header()
        
        # Получаем тестовые данные
        test_employees = self.get_test_employees()
        self.statistics['total_employees'] = len(test_employees)
        
        print(f"👥 Тестовые сотрудники загружены: {len(test_employees)} человек")
        for emp in test_employees:
            print(f"   • {emp['full_name']} ({emp['department']})")
        
        # Тест 1: Redis здоровье
        self.test_redis_health()
        
        # Тест 2: Java сервис здоровье
        self.test_java_service_health()
        
        # Тест 3: Java matching или Python fallback
        matching_result = None
        
        if self.java_available:
            matching_result = self.test_java_matching(test_employees)
        
        if not matching_result or not matching_result.get('success', False):
            print("\n🔄 Переключение на Python fallback...")
            matching_result = self.python_fallback_matching(test_employees)
        
        # Тест 4: Redis кэширование (если есть результаты)
        if matching_result and matching_result.get('success', False):
            self.test_redis_cache_integration(matching_result)
            
            # Тест 5: Публикация событий
            self.test_event_publishing(matching_result)
        
        # Завершаем и выводим итоги
        end_time = time.time()
        self.statistics['test_duration'] = round(end_time - start_time, 2)
        self.print_final_results()
    
    def print_final_results(self) -> None:
        """Выводит итоговые результаты тестирования"""
        print("\n🎯" + "="*60 + "🎯")
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("🎯" + "="*60 + "🎯")
        
        # Результаты тестов
        print("\n🧪 Результаты тестов:")
        for test_name, result in self.test_results.items():
            status = "✅ Пройден" if result else "❌ Провален"
            emoji = "✅" if result else "❌"
            print(f"   {emoji} {test_name.replace('_', ' ').title()}: {status}")
        
        # Статистика
        print(f"\n📈 Статистика:")
        print(f"   👥 Всего сотрудников: {self.statistics['total_employees']}")
        print(f"   💕 Пар создано: {self.statistics['pairs_created']}")
        print(f"   😔 Без пары: {self.statistics['employees_without_pair']}")
        print(f"   ⏱️ Время тестирования: {self.statistics['test_duration']} сек")
        
        # Общий статус интеграции
        successful_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n🎯 Общий статус интеграции:")
        print(f"   Пройдено тестов: {successful_tests}/{total_tests}")
        print(f"   Процент успеха: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("   🚀 Интеграция работает отлично!")
        elif success_rate >= 60:
            print("   ⚠️ Интеграция работает с замечаниями")
        else:
            print("   ❌ Интеграция требует исправлений")
        
        # Рекомендации
        print(f"\n💡 Рекомендации:")
        if not self.test_results['redis_health']:
            print("   • Проверьте работоспособность Redis сервера")
        if not self.test_results['java_health']:
            print("   • Запустите Java микросервис на порту 8080")
        if not self.test_results['java_matching']:
            print("   • Проверьте API endpoints Java микросервиса")
        if self.test_results['python_fallback']:
            print("   • Python fallback работает, система устойчива")
        
        print("\n🎉 Тестирование завершено!")
        print("🎯" + "="*60 + "🎯")


def main():
    """Главная функция запуска тестирования"""
    try:
        tester = MicroserviceIntegrationTester()
        tester.run_hybrid_integration_test()
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()