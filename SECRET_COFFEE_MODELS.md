# 📋 Документация: Система "Тайный кофе"

## 🎯 Описание

Система "Тайный кофе" - это модуль для ConnectBot v21, который автоматически создает пары сотрудников для неформального общения за чашечкой кофе. Система интегрирована с Java микросервисом для алгоритмов matching и использует Django модели для управления данными.

## 📊 Архитектура моделей

### 🏗️ Диаграмма связей

```
SecretCoffee (Сессия)
    ↓ One-to-Many
CoffeePair (Пара)
    ↓ Many-to-One        ↓ Many-to-One
Employee (Сотрудник 1)   Employee (Сотрудник 2)
```

## 📝 Модели данных

### 1. SecretCoffee - Еженедельная сессия тайного кофе

**Назначение**: Управляет еженедельными сессиями создания пар для тайного кофе.

**Основные поля**:
- `week_start` - Дата начала недели (понедельник)
- `title` - Название сессии (авто-генерируется)
- `status` - Статус сессии (draft, active, completed, cancelled)
- `algorithm_used` - Использованный алгоритм matching
- `total_participants` - Общее количество участников
- `successful_pairs` - Количество успешных пар

**Временные рамки**:
- `registration_deadline` - Дедлайн регистрации
- `meeting_deadline` - Дедлайн проведения встреч

**Основные методы**:
- `get_pairs_count()` - Количество созданных пар
- `get_confirmed_pairs_count()` - Количество подтвержденных пар
- `get_participation_rate()` - Процент участия

**Ограничения**:
- Одна сессия на неделю (`unique_together = ['week_start']`)

### 2. CoffeePair - Пара сотрудников

**Назначение**: Представляет пару сотрудников в рамках сессии тайного кофе.

**Участники**:
- `employee1` - Первый сотрудник
- `employee2` - Второй сотрудник
- `secret_coffee` - Связь с сессией

**Подтверждения**:
- `confirmed_employee1` - Подтверждение от первого
- `confirmed_employee2` - Подтверждение от второго

**Чат и встречи**:
- `chat_created` - Создан ли чат
- `chat_id` - ID Telegram чата
- `meeting_scheduled` - Запланирована ли встреча
- `meeting_date` - Дата встречи
- `meeting_place` - Место встречи
- `meeting_completed` - Состоялась ли встреча

**Обратная связь**:
- `feedback_employee1/2` - Отзывы участников
- `rating_employee1/2` - Оценки (1-5)

**Алгоритм**:
- `match_score` - Оценка совместимости (0-1)
- `match_reason` - Причина объединения в пару

**Статусы**:
- `created` - Создана
- `notified` - Уведомления отправлены
- `confirmed` - Подтверждена
- `meeting_scheduled` - Встреча запланирована
- `completed` - Завершена
- `declined` - Отказались
- `expired` - Просрочена

**Основные методы**:
- `is_fully_confirmed()` - Подтвердили ли оба
- `has_feedback_from_both()` - Оставили ли отзыв оба
- `get_average_rating()` - Средняя оценка
- `get_other_employee(current)` - Получить партнера
- `can_be_confirmed_by(employee)` - Может ли подтвердить
- `confirm_by_employee(employee)` - Подтвердить участие

**Ограничения**:
- Уникальная пара в рамках сессии
- Сотрудник не может быть в паре с самим собой

## 🔧 Использование

### Создание сессии

```python
from employees.models import SecretCoffee
from datetime import date, timedelta

# Понедельник текущей недели
today = date.today()
week_start = today - timedelta(days=today.weekday())

session = SecretCoffee.objects.create(
    week_start=week_start,
    status='active',
    algorithm_used='java_microservice',
    total_participants=10
)
```

### Создание пары

```python
from employees.models import Employee, CoffeePair

emp1 = Employee.objects.get(id=1)
emp2 = Employee.objects.get(id=2)

pair = CoffeePair.objects.create(
    secret_coffee=session,
    employee1=emp1,
    employee2=emp2,
    match_score=0.85,
    match_reason="Общие интересы: кофе и технологии"
)
```

### Подтверждение участия

```python
# Подтверждение от конкретного сотрудника
success = pair.confirm_by_employee(emp1)
if success:
    print("Участие подтверждено")

# Проверка статуса
if pair.is_fully_confirmed():
    print("Оба участника подтвердили")
```

### Статистика сессии

```python
session = SecretCoffee.objects.get(week_start=week_start)

print(f"Всего пар: {session.get_pairs_count()}")
print(f"Подтвержденных: {session.get_confirmed_pairs_count()}")
print(f"Процент участия: {session.get_participation_rate()}%")
```

## 🚀 Интеграция с Java микросервисом

### API для создания пар

```python
import requests

def create_pairs_via_java(employees, java_service_url):
    """Создает пары через Java микросервис"""
    
    # Подготовка данных
    java_employees = [
        {
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position or '',
            'department': emp.department.name if emp.department else '',
            'is_active': emp.is_active
        }
        for emp in employees
    ]
    
    # Запрос к Java API
    response = requests.post(
        f"{java_service_url}/api/matching/coffee/simple",
        json=java_employees,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('pairs', [])
    
    return []

def save_java_pairs_to_django(pairs_data, session):
    """Сохраняет пары из Java в Django"""
    
    for pair_data in pairs_data:
        emp1_id = pair_data['employee1']['id']
        emp2_id = pair_data['employee2']['id']
        
        employee1 = Employee.objects.get(id=emp1_id)
        employee2 = Employee.objects.get(id=emp2_id)
        
        CoffeePair.objects.create(
            secret_coffee=session,
            employee1=employee1,
            employee2=employee2,
            match_score=pair_data.get('match_score', 1.0),
            match_reason="Java микросервис matching"
        )
```

## 🎯 Бизнес-логика

### Жизненный цикл пары

1. **Создание** (`created`)
   - Пара создается алгоритмом
   - Автоматически назначается статус "created"

2. **Уведомление** (`notified`) 
   - Участникам отправляются уведомления
   - Устанавливается `notified_at`

3. **Подтверждение** (`confirmed`)
   - Оба участника подтверждают участие
   - Автоматически при `confirmed_employee1=True` и `confirmed_employee2=True`
   - Устанавливается `confirmed_at`

4. **Планирование встречи** (`meeting_scheduled`)
   - Участники договариваются о встрече
   - Заполняются `meeting_date` и `meeting_place`

5. **Завершение** (`completed`)
   - Встреча состоялась
   - Собирается обратная связь
   - Устанавливается `completed_at`

### Автоматические переходы статусов

- При подтверждении обеих сторон: `notified` → `confirmed`
- При планировании встречи: `confirmed` → `meeting_scheduled` 
- При завершении встречи: `meeting_scheduled` → `completed`

## 📊 Админ-панель

### SecretCoffeeAdmin

**Отображаемые поля**:
- Название, дата начала недели, статус
- Количество пар, подтвержденных пар
- Процент участия

**Группировка полей**:
- Основная информация
- Настройки
- Статистика (свернута)
- Системная информация (свернута)

**Inline**: Пары в рамках сессии

### CoffeePairAdmin

**Отображаемые поля**:
- Участники, статус, совместимость
- Подтверждения, чат, встреча

**Группировка полей**:
- Участники
- Подтверждения  
- Чат и встреча
- Алгоритм matching (свернуто)
- Обратная связь (свернуто)
- Временные метки (свернуто)

## 🧪 Тестирование

### Доступные тестовые скрипты

1. **`test_secret_coffee.py`** - Базовое тестирование моделей
   - Создание сотрудников и сессий
   - Формирование пар
   - Симуляция подтверждений и встреч
   - Сбор статистики

2. **`test_coffee_java_integration.py`** - Интеграция с Java
   - Проверка доступности Java микросервиса
   - Создание пар через Java API
   - Сохранение результатов в Django
   - Тестирование методов моделей

### Запуск тестов

```bash
# Активация виртуального окружения
.\venv\Scripts\Activate.ps1

# Базовое тестирование
python test_secret_coffee.py

# Интеграция с Java (требует запущенный Java сервис)
python test_coffee_java_integration.py
```

## 🔍 Индексы и производительность

### Созданные индексы

**SecretCoffee**:
- `(week_start, status)` - Поиск по неделе и статусу
- `(status, created_at)` - Сортировка по времени создания

**CoffeePair**:
- `(secret_coffee, status)` - Пары в рамках сессии
- `(employee1, status)` - Пары конкретного сотрудника
- `(employee2, status)` - Пары конкретного сотрудника
- `(status, created_at)` - Сортировка по времени

### Рекомендации по производительности

- Используйте `select_related('employee1', 'employee2')` при работе с парами
- Кэшируйте статистику сессий при большом количестве пар
- Используйте пагинацию в админ-панели для больших сессий

## 🔐 Безопасность и валидация

### Ограничения модели

- Сотрудник не может быть в паре с самим собой
- Одна сессия на неделю
- Уникальная пара в рамках сессии
- Оценки в диапазоне 1-5

### Рекомендации по безопасности

- Проверяйте права доступа при создании пар
- Логируйте изменения статусов для аудита
- Ограничивайте доступ к персональным данным

## 📈 Аналитика и отчетность

### Доступные метрики

- Процент участия в сессиях
- Средние оценки встреч
- Активность по отделам
- Эффективность алгоритмов matching

### Примеры запросов

```python
from django.db.models import Avg, Count

# Средняя оценка по сессиям
avg_ratings = CoffeePair.objects.exclude(
    rating_employee1__isnull=True,
    rating_employee2__isnull=True
).aggregate(
    avg_rating1=Avg('rating_employee1'),
    avg_rating2=Avg('rating_employee2')
)

# Статистика по отделам
dept_stats = CoffeePair.objects.filter(
    meeting_completed=True
).values(
    'employee1__department__name'
).annotate(
    meetings_count=Count('id')
)
```

## 🎉 Заключение

Система "Тайный кофе" обеспечивает:

✅ **Полную интеграцию** с Java микросервисом для алгоритмов matching  
✅ **Гибкую архитектуру** моделей с поддержкой различных статусов  
✅ **Удобную админ-панель** для управления сессиями и парами  
✅ **Comprehensive тестирование** с демонстрационными скриптами  
✅ **Высокую производительность** благодаря продуманным индексам  
✅ **Безопасность** с валидацией данных и ограничениями  

Система готова к продуктивному использованию в ConnectBot v21! ☕🚀