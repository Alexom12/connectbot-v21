#!/usr/bin/env python3
"""
🧪 Интеграция системы "Тайный кофе" с Java микросервисом
Демонстрирует создание пар через Java API и сохранение в Django модели
"""

import os
import sys
import json
import django
import requests
from datetime import datetime, date, timedelta
from django.utils import timezone

# Настройка Django окружения
def setup_django():
    """Настраивает Django окружение"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

setup_django()

from employees.models import Employee, SecretCoffee, CoffeePair


class SecretCoffeeJavaIntegration:
    """Интеграция тайного кофе с Java микросервисом"""
    
    def __init__(self):
        self.java_service_url = "http://localhost:8080"
        self.employees = []
        self.coffee_session = None
    
    def print_header(self):
        """Выводит заголовок"""
        print("🚀" + "="*60 + "🚀")
        print("☕ ИНТЕГРАЦИЯ ТАЙНОГО КОФЕ С JAVA МИКРОСЕРВИСОМ ☕")
        print("🚀" + "="*60 + "🚀")
        print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Java Service: {self.java_service_url}")
        print()
    
    def check_java_service(self):
        """Проверяет доступность Java микросервиса"""
        print("🔄 Проверка Java микросервиса...")
        try:
            health_url = f"{self.java_service_url}/api/matching/health"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code in [200, 503]:  # UP или DEGRADED
                health_data = response.json()
                print(f"✅ Java сервис доступен")
                print(f"   Сервис: {health_data.get('service')}")
                print(f"   Версия: {health_data.get('version')}")
                print(f"   Статус: {health_data.get('overall_status', health_data.get('status'))}")
                return True
            else:
                print(f"❌ Java сервис недоступен: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка подключения к Java сервису: {e}")
            return False
        
        print()
    
    def get_employees_for_coffee(self):
        """Получает активных сотрудников для тайного кофе"""
        print("👥 Получение сотрудников...")
        
        # Получаем активных авторизованных сотрудников
        self.employees = list(Employee.objects.filter(
            is_active=True,
            authorized=True
        ))
        
        print(f"📊 Найдено активных сотрудников: {len(self.employees)}")
        
        for emp in self.employees:
            print(f"   👤 {emp.full_name} ({emp.position or 'Без должности'})")
        
        print()
        return len(self.employees) >= 2  # Минимум 2 для создания пары
    
    def create_coffee_session(self):
        """Создает сессию тайного кофе"""
        print("☕ Создание сессии тайного кофе...")
        
        # Понедельник текущей недели
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        # Очищаем существующую сессию для демонстрации
        SecretCoffee.objects.filter(week_start=week_start).delete()
        
        self.coffee_session = SecretCoffee.objects.create(
            week_start=week_start,
            title=f'Java-генерированный тайный кофе {week_start.strftime("%d.%m.%Y")}',
            description='Пары созданы через Java микросервис matching',
            status='active',
            algorithm_used='java_microservice',
            registration_deadline=timezone.now() + timedelta(days=2),
            meeting_deadline=week_start + timedelta(days=5),
            total_participants=len(self.employees)
        )
        
        print(f"✅ Создана сессия: {self.coffee_session.title}")
        print(f"   📅 Неделя: {self.coffee_session.week_start}")
        print(f"   🤖 Алгоритм: {self.coffee_session.algorithm_used}")
        print()
    
    def create_pairs_via_java(self):
        """Создает пары через Java микросервис"""
        print("🤝 Создание пар через Java микросервис...")
        
        # Подготавливаем данные для Java API
        java_employees = []
        for emp in self.employees:
            java_emp = {
                'id': emp.id,
                'full_name': emp.full_name,
                'position': emp.position or '',
                'department': getattr(emp.department, 'name', '') if emp.department else '',
                'is_active': emp.is_active
            }
            java_employees.append(java_emp)
        
        print(f"   📤 Отправляем {len(java_employees)} сотрудников в Java API...")
        
        try:
            # Используем простой алгоритм matching
            matching_url = f"{self.java_service_url}/api/matching/coffee/simple"
            
            response = requests.post(
                matching_url,
                json=java_employees,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Java API ответил успешно!")
                print(f"   📊 Статус: {result.get('successful', False)}")
                print(f"   🎲 Алгоритм: {result.get('algorithm', 'unknown')}")
                
                # Обрабатываем результат
                pairs_data = result.get('pairs', [])
                unmatched_data = result.get('unmatched', [])
                
                print(f"   💑 Создано пар: {len(pairs_data)}")
                print(f"   😞 Без пары: {len(unmatched_data)}")
                
                # Сохраняем пары в Django модели
                self.save_java_pairs_to_django(pairs_data)
                
                return True
            else:
                print(f"   ❌ Java API ошибка: HTTP {response.status_code}")
                print(f"   📄 Ответ: {response.text[:200]}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ошибка запроса к Java API: {e}")
            return False
    
    def save_java_pairs_to_django(self, pairs_data):
        """Сохраняет пары из Java API в Django модели"""
        print("   💾 Сохранение пар в Django...")
        
        saved_pairs = 0
        for pair_data in pairs_data:
            try:
                # Извлекаем данные сотрудников
                emp1_data = pair_data.get('employee1', {})
                emp2_data = pair_data.get('employee2', {})
                
                emp1_id = emp1_data.get('id')
                emp2_id = emp2_data.get('id')
                
                if not emp1_id or not emp2_id:
                    print(f"      ⚠️ Пропускаем пару - отсутствуют ID сотрудников")
                    continue
                
                # Получаем сотрудников из базы
                try:
                    employee1 = Employee.objects.get(id=emp1_id)
                    employee2 = Employee.objects.get(id=emp2_id)
                except Employee.DoesNotExist as e:
                    print(f"      ⚠️ Сотрудник не найден: {e}")
                    continue
                
                # Создаем пару
                coffee_pair = CoffeePair.objects.create(
                    secret_coffee=self.coffee_session,
                    employee1=employee1,
                    employee2=employee2,
                    match_score=pair_data.get('match_score', 1.0),
                    match_reason=f"Java алгоритм: {self.coffee_session.algorithm_used}",
                    status='created'
                )
                
                saved_pairs += 1
                print(f"      ✅ Пара {saved_pairs}: {employee1.full_name} ↔ {employee2.full_name}")
                print(f"         🎯 Score: {coffee_pair.match_score}")
                
            except Exception as e:
                print(f"      ❌ Ошибка создания пары: {e}")
        
        print(f"   📊 Сохранено пар в Django: {saved_pairs}")
        
        # Обновляем статистику сессии
        self.coffee_session.successful_pairs = saved_pairs
        self.coffee_session.save()
        
        print()
    
    def demonstrate_django_models(self):
        """Демонстрирует работу с Django моделями"""
        print("🧪 Демонстрация Django моделей...")
        
        # Получаем статистику сессии
        total_pairs = self.coffee_session.get_pairs_count()
        
        print(f"📊 Статистика сессии:")
        print(f"   🆔 ID сессии: {self.coffee_session.id}")
        print(f"   📋 Название: {self.coffee_session.title}")
        print(f"   📅 Неделя: {self.coffee_session.week_start}")
        print(f"   🤖 Алгоритм: {self.coffee_session.algorithm_used}")
        print(f"   💑 Пар создано: {total_pairs}")
        print()
        
        # Демонстрируем работу с парами
        if total_pairs > 0:
            print("💑 Созданные пары:")
            pairs = self.coffee_session.coffee_pairs.all()
            
            for i, pair in enumerate(pairs, 1):
                print(f"   {i}. {pair}")
                print(f"      🆔 ID: {pair.id}")
                print(f"      🎯 Score: {pair.match_score}")
                print(f"      📊 Статус: {pair.get_status_display()}")
                print(f"      💭 Причина: {pair.match_reason}")
                
                # Демонстрируем методы модели
                print(f"      🔄 Может подтвердить {pair.employee1.full_name}: {pair.can_be_confirmed_by(pair.employee1)}")
                print(f"      🔄 Может подтвердить {pair.employee2.full_name}: {pair.can_be_confirmed_by(pair.employee2)}")
        
        print()
    
    def test_model_methods(self):
        """Тестирует методы моделей"""
        print("🧪 Тестирование методов моделей...")
        
        pairs = self.coffee_session.coffee_pairs.all()
        if pairs.exists():
            # Берем первую пару для демонстрации
            test_pair = pairs.first()
            
            print(f"🔍 Тестируем пару: {test_pair}")
            print()
            
            # Тест подтверждения от первого сотрудника
            print("✅ Подтверждение от первого сотрудника...")
            success = test_pair.confirm_by_employee(test_pair.employee1)
            print(f"   Результат: {'✅ Успешно' if success else '❌ Не удалось'}")
            print(f"   Статус пары: {test_pair.get_status_display()}")
            
            # Тест подтверждения от второго сотрудника  
            print("✅ Подтверждение от второго сотрудника...")
            success = test_pair.confirm_by_employee(test_pair.employee2)
            print(f"   Результат: {'✅ Успешно' if success else '❌ Не удалось'}")
            print(f"   Статус пары: {test_pair.get_status_display()}")
            print(f"   Полностью подтверждена: {'✅ Да' if test_pair.is_fully_confirmed() else '❌ Нет'}")
            
            # Обновляем статистику сессии
            print(f"\n📊 Обновленная статистика сессии:")
            print(f"   💑 Всего пар: {self.coffee_session.get_pairs_count()}")
            print(f"   ✅ Подтвержденных: {self.coffee_session.get_confirmed_pairs_count()}")
            print(f"   📈 Участие: {self.coffee_session.get_participation_rate()}%")
        
        print()
    
    def run_integration_demo(self):
        """Запускает полную демонстрацию интеграции"""
        self.print_header()
        
        # Проверяем Java сервис
        java_available = self.check_java_service()
        
        if not java_available:
            print("❌ Java микросервис недоступен. Завершаем демонстрацию.")
            return False
        
        # Получаем сотрудников
        if not self.get_employees_for_coffee():
            print("❌ Недостаточно сотрудников для создания пар.")
            return False
        
        # Создаем сессию
        self.create_coffee_session()
        
        # Создаем пары через Java
        if self.create_pairs_via_java():
            # Демонстрируем Django модели
            self.demonstrate_django_models()
            
            # Тестируем методы моделей
            self.test_model_methods()
            
            print("🎉 Интеграция завершена успешно!")
        else:
            print("❌ Не удалось создать пары через Java микросервис")
        
        print("🚀" + "="*60 + "🚀")


def main():
    """Главная функция"""
    try:
        integration = SecretCoffeeJavaIntegration()
        integration.run_integration_demo()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()