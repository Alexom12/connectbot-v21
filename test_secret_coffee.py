#!/usr/bin/env python3
"""
🧪 Тестовый скрипт системы "Тайный кофе"
Демонстрирует работу с новыми моделями SecretCoffee и CoffeePair
"""

import os
import sys
import django
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


class SecretCoffeeDemo:
    """Демонстрация системы тайного кофе"""
    
    def __init__(self):
        self.employees = []
        self.coffee_session = None
    
    def print_header(self):
        """Выводит заголовок"""
        print("☕" + "="*60 + "☕")
        print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ 'ТАЙНЫЙ КОФЕ' 🧪")
        print("☕" + "="*60 + "☕")
        print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def create_test_employees(self):
        """Создает тестовых сотрудников если их нет"""
        test_data = [
            {
                'full_name': 'Александр Петров',
                'position': 'Senior Developer',
                'department': 'IT',
                'telegram_username': 'alex_dev'
            },
            {
                'full_name': 'Мария Иванова', 
                'position': 'Product Manager',
                'department': 'Product',
                'telegram_username': 'maria_pm'
            },
            {
                'full_name': 'Дмитрий Сидоров',
                'position': 'UI/UX Designer', 
                'department': 'Design',
                'telegram_username': 'dmitry_design'
            },
            {
                'full_name': 'Елена Козлова',
                'position': 'QA Engineer',
                'department': 'QA',
                'telegram_username': 'elena_qa'
            },
            {
                'full_name': 'Игорь Волков',
                'position': 'DevOps Engineer',
                'department': 'Infrastructure',
                'telegram_username': 'igor_devops'
            },
            {
                'full_name': 'Анна Морозова',
                'position': 'Business Analyst',
                'department': 'Analytics',
                'telegram_username': 'anna_ba'
            }
        ]
        
        print("👥 Создание тестовых сотрудников...")
        created_count = 0
        
        for emp_data in test_data:
            employee, created = Employee.objects.get_or_create(
                full_name=emp_data['full_name'],
                defaults={
                    'position': emp_data['position'],
                    'telegram_username': emp_data['telegram_username'],
                    'is_active': True,
                    'authorized': True
                }
            )
            
            if created:
                print(f"   ✅ Создан: {employee.full_name}")
                created_count += 1
            else:
                print(f"   ℹ️ Существует: {employee.full_name}")
            
            self.employees.append(employee)
        
        print(f"📊 Создано новых сотрудников: {created_count}")
        print(f"👨‍💼 Всего доступных сотрудников: {len(self.employees)}")
        print()
    
    def create_coffee_session(self):
        """Создает новую сессию тайного кофе"""
        print("☕ Создание сессии тайного кофе...")
        
        # Понедельник текущей недели
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        self.coffee_session, created = SecretCoffee.objects.get_or_create(
            week_start=week_start,
            defaults={
                'title': f'Тайный кофе на неделю {week_start.strftime("%d.%m.%Y")}',
                'description': 'Еженедельная сессия знакомств за чашечкой кофе',
                'status': 'active',
                'max_pairs': 50,
                'algorithm_used': 'simple_random',
                'registration_deadline': timezone.now() + timedelta(days=2),
                'meeting_deadline': week_start + timedelta(days=5),  # Пятница
                'total_participants': len(self.employees)
            }
        )
        
        if created:
            print(f"   ✅ Создана новая сессия: {self.coffee_session.title}")
        else:
            print(f"   ℹ️ Используется существующая сессия: {self.coffee_session.title}")
        
        print(f"   📅 Неделя: {self.coffee_session.week_start}")
        print(f"   📊 Статус: {self.coffee_session.get_status_display()}")
        print(f"   ⏰ Дедлайн регистрации: {self.coffee_session.registration_deadline}")
        print(f"   🎯 Дедлайн встреч: {self.coffee_session.meeting_deadline}")
        print()
    
    def create_coffee_pairs(self):
        """Создает пары для тайного кофе"""
        print("🤝 Создание пар сотрудников...")
        
        # Очищаем существующие пары для демонстрации
        existing_pairs = self.coffee_session.coffee_pairs.count()
        if existing_pairs > 0:
            print(f"   🗑️ Удаление {existing_pairs} существующих пар")
            self.coffee_session.coffee_pairs.all().delete()
        
        # Создаем пары (простой алгоритм)
        import random
        available_employees = self.employees.copy()
        random.shuffle(available_employees)
        
        pairs_created = 0
        for i in range(0, len(available_employees) - 1, 2):
            emp1 = available_employees[i]
            emp2 = available_employees[i + 1]
            
            # Симулируем оценку совместимости
            match_score = random.uniform(0.6, 0.95)
            
            # Определяем причину объединения
            reasons = [
                "Разные отделы - хорошая возможность для cross-functional общения",
                "Схожие роли - можно обменяться опытом",
                "Случайное совпадение алгоритма",
                "Оба новички в компании",
                "Оптимальное географическое расположение"
            ]
            
            pair = CoffeePair.objects.create(
                secret_coffee=self.coffee_session,
                employee1=emp1,
                employee2=emp2,
                match_score=match_score,
                match_reason=random.choice(reasons),
                status='created'
            )
            
            pairs_created += 1
            print(f"   💑 Пара {pairs_created}: {emp1.full_name} ↔ {emp2.full_name}")
            print(f"      🎯 Совместимость: {match_score:.2f}")
            print(f"      💭 Причина: {pair.match_reason}")
        
        # Если нечетное количество сотрудников
        if len(available_employees) % 2 == 1:
            unpaired = available_employees[-1]
            print(f"   😞 Без пары: {unpaired.full_name}")
        
        print(f"📊 Создано пар: {pairs_created}")
        print()
    
    def simulate_confirmations(self):
        """Симулирует подтверждения от сотрудников"""
        print("✅ Симуляция подтверждений участия...")
        
        pairs = self.coffee_session.coffee_pairs.all()
        confirmed_pairs = 0
        
        for pair in pairs:
            # Симулируем различные сценарии подтверждений
            import random
            
            # 80% шанс подтверждения от первого сотрудника
            if random.random() < 0.8:
                pair.confirmed_employee1 = True
                
            # 75% шанс подтверждения от второго сотрудника  
            if random.random() < 0.75:
                pair.confirmed_employee2 = True
            
            # Обновляем статус
            if pair.confirmed_employee1 and pair.confirmed_employee2:
                pair.status = 'confirmed'
                pair.confirmed_at = timezone.now()
                confirmed_pairs += 1
                print(f"   ✅ {pair.employee1.full_name} ↔ {pair.employee2.full_name}")
            elif pair.confirmed_employee1 or pair.confirmed_employee2:
                pair.status = 'notified'
                print(f"   ⏳ {pair.employee1.full_name} ↔ {pair.employee2.full_name} (частично)")
            else:
                print(f"   ❌ {pair.employee1.full_name} ↔ {pair.employee2.full_name} (не подтвердили)")
            
            pair.save()
        
        print(f"📊 Полностью подтвержденных пар: {confirmed_pairs}/{len(pairs)}")
        print()
    
    def simulate_meetings_and_feedback(self):
        """Симулирует встречи и обратную связь"""
        print("📅 Симуляция встреч и обратной связи...")
        
        confirmed_pairs = self.coffee_session.coffee_pairs.filter(status='confirmed')
        completed_meetings = 0
        
        places = [
            "Кафе 'Старбакс' на 1 этаже",
            "Кухня в офисе", 
            "Ресторан 'Тануки' рядом с офисом",
            "Парк Сокольники",
            "Антикафе 'Время есть'",
            "Коворкинг на Красной площади"
        ]
        
        for pair in confirmed_pairs:
            import random
            
            # Симулируем планирование встречи (90% шанс)
            if random.random() < 0.9:
                pair.meeting_scheduled = True
                pair.meeting_date = timezone.now() + timedelta(
                    days=random.randint(1, 5),
                    hours=random.randint(12, 18)
                )
                pair.meeting_place = random.choice(places)
                
                # Симулируем проведение встречи (85% шанс)
                if random.random() < 0.85:
                    pair.meeting_completed = True
                    pair.completed_at = timezone.now()
                    pair.status = 'completed'
                    completed_meetings += 1
                    
                    # Генерируем обратную связь
                    feedbacks = [
                        "Отличное общение! Узнал много нового о работе другого отдела.",
                        "Приятная встреча, нашли общие интересы.",
                        "Полезный нетворкинг, обменялись контактами.",
                        "Интересно пообщаться с коллегой из другой команды.",
                        "Хорошая инициатива, стоит повторить!"
                    ]
                    
                    if random.random() < 0.7:  # 70% оставляют отзыв
                        pair.feedback_employee1 = random.choice(feedbacks)
                        pair.rating_employee1 = random.randint(4, 5)
                    
                    if random.random() < 0.7:
                        pair.feedback_employee2 = random.choice(feedbacks) 
                        pair.rating_employee2 = random.randint(3, 5)
                    
                    print(f"   ✅ Встреча: {pair.employee1.full_name} ↔ {pair.employee2.full_name}")
                    print(f"      📍 Место: {pair.meeting_place}")
                    print(f"      📅 Дата: {pair.meeting_date.strftime('%d.%m %H:%M')}")
                    if pair.get_average_rating():
                        print(f"      ⭐ Средняя оценка: {pair.get_average_rating():.1f}")
                else:
                    pair.status = 'meeting_scheduled'
                    print(f"   📅 Запланирована: {pair.employee1.full_name} ↔ {pair.employee2.full_name}")
            
            pair.save()
        
        print(f"📊 Завершенных встреч: {completed_meetings}/{len(confirmed_pairs)}")
        print()
    
    def show_statistics(self):
        """Показывает статистику сессии"""
        print("📊 СТАТИСТИКА СЕССИИ")
        print("-" * 40)
        
        total_pairs = self.coffee_session.get_pairs_count()
        confirmed_pairs = self.coffee_session.get_confirmed_pairs_count()
        participation_rate = self.coffee_session.get_participation_rate()
        
        print(f"📋 Название: {self.coffee_session.title}")
        print(f"📅 Неделя: {self.coffee_session.week_start}")
        print(f"📊 Статус: {self.coffee_session.get_status_display()}")
        print(f"👥 Участников: {self.coffee_session.total_participants}")
        print(f"💑 Всего пар: {total_pairs}")
        print(f"✅ Подтвержденных пар: {confirmed_pairs}")
        print(f"📈 Процент участия: {participation_rate}%")
        
        # Статистика по статусам пар
        print(f"\n📋 Статусы пар:")
        from django.db.models import Count
        status_stats = self.coffee_session.coffee_pairs.values('status').annotate(count=Count('id'))
        
        for stat in status_stats:
            status_display = dict(CoffeePair.STATUS_CHOICES).get(stat['status'], stat['status'])
            print(f"   {status_display}: {stat['count']}")
        
        # Статистика встреч
        completed_meetings = self.coffee_session.coffee_pairs.filter(meeting_completed=True).count()
        print(f"\n📅 Завершенных встреч: {completed_meetings}")
        
        # Средняя оценка
        pairs_with_ratings = self.coffee_session.coffee_pairs.exclude(
            rating_employee1__isnull=True, rating_employee2__isnull=True
        )
        if pairs_with_ratings:
            total_ratings = 0
            rating_count = 0
            for pair in pairs_with_ratings:
                avg = pair.get_average_rating()
                if avg:
                    total_ratings += avg
                    rating_count += 1
            
            if rating_count > 0:
                overall_rating = total_ratings / rating_count
                print(f"⭐ Средняя оценка сессии: {overall_rating:.2f}/5")
        
        print()
    
    def run_demo(self):
        """Запускает полную демонстрацию"""
        self.print_header()
        
        print("🔄 Этапы демонстрации:")
        print("1️⃣ Создание тестовых сотрудников")
        print("2️⃣ Создание сессии тайного кофе")
        print("3️⃣ Формирование пар")
        print("4️⃣ Подтверждение участия")
        print("5️⃣ Планирование встреч")
        print("6️⃣ Сбор статистики")
        print()
        
        # Выполняем этапы
        self.create_test_employees()
        self.create_coffee_session()
        self.create_coffee_pairs()
        self.simulate_confirmations()
        self.simulate_meetings_and_feedback()
        self.show_statistics()
        
        print("🎉 Демонстрация завершена!")
        print("☕" + "="*60 + "☕")


def main():
    """Главная функция"""
    try:
        demo = SecretCoffeeDemo()
        demo.run_demo()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()