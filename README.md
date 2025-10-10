# ConnectBot v21 🤖

Корпоративный Telegram бот для организации активностей и взаимодействия сотрудников.

## 🚀 Функциональность

- **Авторизация сотрудников** через Telegram username
- **Управление интересами** и подписками на активности  
- **Система уведомлений** о новых мероприятиях
- **Достижения и геймификация** участия
- **Админ-панель Django** для управления данными
- **Автоматическое планирование** активностей

## 🛠 Технологии

- **Python 3.13** + **Django 4.2.25**
- **python-telegram-bot 20.0**
- **SQLite** база данных
- **Redis** для кеширования и сессий (опционально)
- **Docker Compose** для Redis
- **PowerShell** скрипты автоматизации

## 📋 Установка и запуск

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

### 7. Запуск сервисов

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
```

## 📝 TODO

- [ ] Добавить больше типов активностей
- [ ] Реализовать систему рейтингов
- [ ] Интеграция с календарем
- [ ] Push-уведомления
- [ ] Мобильное приложение

## 🤝 Поддержка

По вопросам разработки и использования:
- 📧 Email: dev@connectbot.local
- 💬 Telegram: @connectbot_support

## 📄 Лицензия

Проект разработан для внутреннего использования компании.

---
*ConnectBot v21 - Connecting colleagues, one activity at a time! 🎉*

