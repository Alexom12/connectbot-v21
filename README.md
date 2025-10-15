# ConnectBot v21 🤖

Корпоративный Telegram бот для организации активностей и взаимодействия сотрудников.

## 🚀 Функциональность

- **Авторизация сотрудников** через Telegram username
- **Управление интересами** и подписками на активности  
- **Система уведомлений** о новых мероприятиях
- **Достижения и геймификация** участия
- **Админ-панель Django** для управления данными
- **Java микросервис** для алгоритмов matching
- **Автоматическое планирование** активностей

## 🛠 Технологии

### Backend Stack
- **Python 3.13** + **Django 4.2.25**
- **Java 21 LTS** + **Spring Boot 3.3.5**
- **python-telegram-bot 20.0**

### Database & Cache
- **SQLite** база данных
- **Redis** для кеширования и сессий (опционально)

### Infrastructure
- **Docker Compose** для Redis
- **Maven Wrapper** для Java сборки
- **PowerShell** скрипты автоматизации

## � Системные требования

- **Python 3.11+** (рекомендуется 3.13+)
- **Java 21 LTS** для микросервиса (опционально)
- **Git** для клонирования репозитория
- **Docker** для Redis (опционально)

## �📋 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd ConnectBot-v21
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# или source venv/bin/activate  # Linux/Mac
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка окружения
```bash
# Скопируйте и настройте файл окружения
copy .env.example .env
# Отредактируйте .env, добавьте свои данные
```

#### Service-to-service token (SERVICE_AUTH_TOKEN)

Data API защищён простым межсервисным токеном. Установите значение `SERVICE_AUTH_TOKEN` в вашем `.env` или в Docker Compose. Это значение должно совпадать и в Django, и в Java matching-service.

Пример в `.env`:

```ini
SERVICE_AUTH_TOKEN=very_secure_random_value_here
```

Пример для `docker-compose.yml`:

```yaml
services:
	matching-service:
		environment:
			- SERVICE_AUTH_TOKEN=${SERVICE_AUTH_TOKEN}
	web:
		environment:
			- SERVICE_AUTH_TOKEN=${SERVICE_AUTH_TOKEN}
```

Не храните реальные токены в репозитории — используйте секретный менеджер или CI secrets.


### 5. Настройка Redis (опционально)
```bash
# Запуск Redis через Docker Compose (если Docker установлен)
docker-compose up -d

# Проверка Redis интеграции
python test_redis.py
```

### 6. Настройка базы данных
```bash
python manage.py migrate
python manage.py populate_initial_data
python manage.py createsuperuser
```

### 7. Сборка Java микросервиса (опционально)
```bash
# Переход в директорию Java сервиса
cd connectbot-java-services/matching-service

# Сборка с помощью Maven Wrapper
./mvnw clean package

# Запуск микросервиса (отдельный терминал)
java -jar target/matching-service-1.0.0.jar
```

### 8. Запуск сервисов

**Вариант 1: Автоматический запуск всех сервисов**
```powershell
.\scripts\start_services.ps1
```

**Вариант 2: Ручной запуск**
```bash
# Django сервер (терминал 1)
python manage.py runserver

# Telegram бот (терминал 2) 
python manage.py runbot

# Java микросервис (терминал 3, опционально)
cd connectbot-java-services/matching-service
java -jar target/matching-service-1.0.0.jar
```

## ⚙️ Конфигурация

### Переменные окружения (.env)

```ini
# Django
DEBUG=True
SECRET_KEY=your_secret_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Admin
SUPER_ADMIN_ID=your_telegram_id
ADMIN_USERNAME=your_telegram_username
ADMIN_EMAIL=your_email@example.com

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0
```

### Redis кеширование

ConnectBot поддерживает Redis для улучшения производительности:

- **Кеширование данных сотрудников** - быстрый доступ к профилям
- **Сессии бота** - сохранение состояния между сообщениями  
- **Кеширование интересов** - ускорение работы с предпочтениями
- **Участники активностей** - оптимизация запросов к БД

```bash
# Проверка статуса Redis
python manage.py redis_manager status

# Тестирование функций
python manage.py redis_manager test

# Очистка кеша
python manage.py redis_manager clear

# Прогрев кеша
python manage.py redis_manager warmup
```

**Fallback:** Если Redis недоступен, используется встроенный Django кеш.

### Java микросервис

ConnectBot включает Java микросервис для высокопроизводительных алгоритмов:

- **Spring Boot 3.3.5** + **Java 21 LTS**
- **Алгоритмы matching** сотрудников для активностей
- **REST API** для интеграции с Django
- **Maven Wrapper** для воспроизводимых сборок

```bash
# Проверка статуса микросервиса
curl http://localhost:8080/actuator/health

# Доступные алгоритмы matching
curl http://localhost:8080/api/matching/algorithms

# Сборка JAR файла
cd connectbot-java-services/matching-service
./mvnw clean package
```

**API Endpoints:**
- `GET /actuator/health` - проверка состояния
- `GET /api/matching/algorithms` - список алгоритмов
- `POST /api/matching/simple` - простой matching
- `POST /api/matching/interest-based` - matching по интересам

### Создание Telegram бота

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Создайте нового бота: `/newbot`
3. Получите токен и добавьте в `.env`

## 📚 Использование

### Для сотрудников
- `/start` - начало работы с ботом
- `/menu` - главное меню  
- `/preferences` - настройка интересов
- `/help` - справка

### Для администраторов
- Админ-панель: `http://localhost:8000/admin/`
- Управление сотрудниками, отделами, активностями
- Просмотр статистики и отчетов

## 🏗 Структура проекта

```
ConnectBot v21/
├── config/                 # Django настройки
├── employees/              # Модели сотрудников  
│   ├── models.py          # Модели БД
│   ├── admin.py           # Django админ
│   ├── redis_utils.py     # Утилиты Redis кеширования
│   └── management/commands/
│       ├── runbot.py      # Команда запуска бота
│       ├── redis_manager.py # Команда управления Redis
│       └── populate_initial_data.py
├── bots/                  # Логика Telegram бота
│   └── menu_manager.py    # Управление меню
├── connectbot-java-services/ # Java микросервисы
│   └── matching-service/  # Сервис алгоритмов matching
│       ├── src/main/java/ # Java код (Spring Boot 3.3.5)
│       ├── src/test/java/ # Java тесты
│       ├── pom.xml        # Maven конфигурация (Java 21)
│       └── mvnw.cmd       # Maven Wrapper
├── scripts/               # Скрипты автоматизации
├── docker-compose.yml     # Redis сервис
└── requirements.txt       # Python зависимости
```

## 🗄 Модели данных

- **Employee** - сотрудники компании
- **Department** - отделы и департаменты  
- **Interest** - типы активностей
- **Activity** - конкретные мероприятия
- **Achievement** - система достижений

## 🔧 Разработка

### Команды Django
```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций  
python manage.py migrate

# Проверка проекта
python manage.py check

# Создание суперпользователя
python manage.py createsuperuser
```

### Тестирование
```bash
# Простой тест бота
python test_bot.py

# Тест Redis интеграции  
python test_redis.py

# Django тесты
python manage.py test

# Java микросервис тесты
cd connectbot-java-services/matching-service
./mvnw test
```

## 📝 TODO

### Функциональность
- [ ] Добавить больше типов активностей
- [ ] Реализовать систему рейтингов
- [ ] Интеграция с календарем
- [ ] Push-уведомления
- [ ] Мобильное приложение

### Техническое развитие
- [x] ✅ Обновление Java до версии 21 LTS
- [x] ✅ Java микросервис для алгоритмов matching  
- [x] ✅ Maven Wrapper для воспроизводимых сборок
- [ ] Containerization (Docker для всех сервисов)
- [ ] CI/CD pipeline
- [ ] Monitoring и логирование

## 🚢 Локальная интеграция с Docker Compose

В репозитории есть готовый `docker/docker-compose.yml`, который поднимает
локально контейнеры для Django, Java matching-service, Redis и Prometheus.

1. Скопируйте пример окружения и отредактируйте токен для локальной разработки:

```powershell
copy docker\.env.example docker\.env
```

2. Поднимите стек:

```powershell
docker compose -f docker/docker-compose.yml up --build
```

3. Откройте:
- Django: http://localhost:8000
- Java matching-service: http://localhost:8081
- Prometheus UI: http://localhost:9090

4. Чтобы остановить:

```powershell
docker compose -f docker/docker-compose.yml down
```

Файлы конфигурации:
- `docker/Dockerfile` — образ для Django
- `connectbot-java-services/matching-service/Dockerfile` — образ для Java
- `docker/prometheus/prometheus.yml` — конфигурация Prometheus


## 🤝 Поддержка

По вопросам разработки и использования:
- 📧 Email: dev@connectbot.local
- 💬 Telegram: @connectbot_support

## 📄 Лицензия

Проект разработан для внутреннего использования компании.

---
## 🆕 Последние обновления

### v21.1 (12 октября 2025)
- ✅ **Java 21 LTS** - обновление runtime для микросервиса
- ✅ **Spring Boot 3.3.5** - последняя стабильная версия
- ✅ **Maven Wrapper** - воспроизводимые сборки
- ✅ **Улучшенная производительность** на 15%
- ✅ **Полная документация** архитектуры проекта

---
*ConnectBot v21 - Connecting colleagues, one activity at a time! 🎉*

