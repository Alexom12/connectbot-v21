# ConnectBot Matching Service 🤖☕

Spring Boot микросервис алгоритмов matching для ConnectBot v21.

## 🚀 Функциональность

- **Простой случайный matching** - случайное создание пар сотрудников
- **Matching по интересам** - создание пар с учетом общих интересов
- **Межотдельческий matching** - избегание коллег из одного отдела
- **Health Check API** - мониторинг состояния сервиса
- **Redis интеграция** - кеширование и производительность

## 🛠 Технологии

- **Spring Boot 3.2.0** + **Java 17**
- **Spring Web** - REST API
- **Spring Data Redis** - кеширование
- **Spring Actuator** - мониторинг
- **Maven** - управление зависимостями
- **JUnit 5** - тестирование

## 📋 API Endpoints

### Matching Algorithms

#### POST `/api/matching/coffee/simple`
Простой случайный matching

**Request Body:**
```json
[
  {
    "id": 1,
    "full_name": "Иван Иванов",
    "position": "Разработчик",
    "department": "IT",
    "business_center": "БЦ1",
    "telegram_id": 123456789,
    "telegram_username": "ivan",
    "interests": ["coffee", "chess"],
    "is_active": true
  }
]
```

**Response:**
```json
{
  "pairs": [
    {
      "employee1": { ... },
      "employee2": { ... },
      "match_score": 1.0
    }
  ],
  "unmatched": [],
  "algorithm": "SIMPLE_RANDOM",
  "total_employees": 4,
  "total_pairs": 2,
  "success_rate": 100.0,
  "created_at": "2025-10-09T12:00:00"
}
```

#### POST `/api/matching/coffee/interest?interest=coffee`
Matching по интересам

#### POST `/api/matching/coffee/cross-department`
Межотдельческий matching

### Information & Health

#### GET `/api/matching/algorithms`
Список доступных алгоритмов

#### GET `/api/matching/health`
Проверка здоровья сервиса

#### GET `/api/matching/health/detailed`
Детальная информация о состоянии

## 🏗 Структура проекта

```
matching-service/
├── src/main/java/com/connectbot/matching/
│   ├── MatchingServiceApplication.java     # Главный класс
│   ├── controller/
│   │   ├── SimpleMatchingController.java   # REST API
│   │   └── HealthController.java          # Health checks
│   ├── service/
│   │   └── MatchingService.java           # Алгоритмы matching
│   ├── model/
│   │   ├── Employee.java                  # Модель сотрудника
│   │   ├── EmployeePair.java             # Пара сотрудников
│   │   └── MatchingResult.java           # Результат matching
│   └── config/
│       ├── RedisConfig.java              # Конфигурация Redis
│       └── WebConfig.java                # CORS настройки
├── src/main/resources/
│   └── application.properties            # Конфигурация
├── src/test/java/                        # Тесты
└── pom.xml                              # Maven зависимости
```

## 📦 Установка и запуск

### 1. Требования
- Java 17+
- Maven 3.6+
- Redis (опционально)

### 2. Сборка проекта
```bash
cd connectbot-java-services/matching-service
mvn clean compile
```

### 3. Запуск тестов
```bash
mvn test
```

### 4. Запуск сервиса
```bash
# Запуск через Maven
mvn spring-boot:run

# Или через JAR
mvn clean package
java -jar target/matching-service-1.0.0.jar
```

### 5. Проверка работы
```bash
# Health check
curl http://localhost:8080/api/matching/health

# Список алгоритмов
curl http://localhost:8080/api/matching/algorithms
```

## ⚙️ Конфигурация

### application.properties

```properties
# Сервер
server.port=8080

# Redis (опционально)
spring.data.redis.host=localhost
spring.data.redis.port=6379
spring.data.redis.database=1

# Логирование
logging.level.com.connectbot.matching=DEBUG

# Health checks
management.endpoints.web.exposure.include=health,info,metrics
management.endpoint.health.show-details=always
```

### Docker (опционально)

```yaml
# Добавить в docker-compose.yml
matching-service:
  build: ./connectbot-java-services/matching-service
  ports:
    - "8080:8080"
  depends_on:
    - redis
  environment:
    - SPRING_DATA_REDIS_HOST=redis
```

## 🧪 Тестирование

### Unit тесты
```bash
mvn test
```

### Integration тесты  
```bash
mvn verify
```

### Тест API через curl
```bash
# Простой matching
curl -X POST http://localhost:8080/api/matching/coffee/simple \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": 1,
      "full_name": "Test User 1",
      "interests": ["coffee"],
      "is_active": true
    },
    {
      "id": 2, 
      "full_name": "Test User 2",
      "interests": ["coffee"],
      "is_active": true
    }
  ]'
```

## 🔧 Алгоритмы Matching

### 1. Simple Random (SIMPLE_RANDOM)
- Случайное перемешивание сотрудников
- Создание пар в порядке очереди
- Нечетное количество → один остается без пары

### 2. Interest Based (INTEREST_BASED)  
- Фильтрация по конкретному интересу
- Применение простого алгоритма к отфильтрованным
- Подходит для тематических активностей

### 3. Cross Department (CROSS_DEPARTMENT)
- Избегание коллег из одного отдела
- Приоритет парам из разных отделов
- Способствует межотдельческому общению

## 📊 Мониторинг

### Health Checks
- `/api/matching/health` - базовые проверки
- `/api/matching/health/detailed` - расширенная информация
- Проверка Redis подключения
- Мониторинг памяти и ресурсов

### Логирование
- Все matching операции логируются
- Уровни: DEBUG, INFO, WARN, ERROR
- Структурированные логи для мониторинга

## 🚀 Production Ready

- ✅ Exception handling
- ✅ Input validation  
- ✅ Health checks
- ✅ CORS поддержка
- ✅ Redis интеграция
- ✅ Comprehensive testing
- ✅ Production logging

---

**Версия:** 1.0.0  
**Порт:** 8080  
**Статус:** ✅ Production Ready