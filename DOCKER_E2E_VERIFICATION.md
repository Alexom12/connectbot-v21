# Docker Compose E2E verification (short)

Краткий отчёт о выполненных E2E проверках для `connectbot-v21` (docker-compose).

Что сделано
- Подключил `matching-service` к Python/Django Data API и проверил работу под Docker Compose.
- Исправлены проблемы сборки (удалён go-offline шаг и временный surefire plugin), исправлен NPE в `MatchingService` (constructor injection).
- Созданы тестовые сотрудники и interest в Django и выполнён E2E POST тест — matching-service вернул непустые пары.

Как воспроизвести (на сервере или локально, из корня репозитория)

1) Убедитесь, что в корне репозитория присутствует `.env` с переменной `SERVICE_AUTH_TOKEN` и `DATAAPI_BASE_URL` (см. `docker/.env.example`).

2) Поднять контейнеры (в папке `docker`):

```bash
cd docker
sudo docker compose -f docker-compose.yml up -d --build
```

3) Проверить health endpoint matching-service:

```bash
curl -sS http://127.0.0.1:8081/actuator/health | jq .
```

4) Создать тестовых сотрудников (пример, в контейнере `web`):

```bash
sudo docker compose -f docker/docker-compose.yml exec web python manage.py shell -c "from employees.models import Employee, Interest, EmployeeInterest; i, _ = Interest.objects.get_or_create(code='coffee', defaults={'name':'Тайный кофе'}); e1, _ = Employee.objects.get_or_create(external_id='1', defaults={'full_name':'Test User One'}); e2, _ = Employee.objects.get_or_create(external_id='2', defaults={'full_name':'Test User Two'}); EmployeeInterest.objects.get_or_create(employee=e1, interest=i); EmployeeInterest.objects.get_or_create(employee=e2, interest=i)"
```

5) Запрос к Data API (на машине, где доступен `web` по 127.0.0.1:8000):

```bash
echo '{}' | curl -sS -H 'Content-Type: application/json' -H 'Authorization: Service $SERVICE_AUTH_TOKEN' -d @- http://127.0.0.1:8000/api/v1/data/employees-for-matching | jq .
```

Ожидаемый ответ: JSON с полем `employees` содержащим созданных сотрудников.

6) Вызов matching-service (правильный формат JSON):

```bash
echo '{"algorithm_type":"any"}' | curl -sS -H 'Content-Type: application/json' -d @- http://127.0.0.1:8081/api/v1/matching/match/secret-coffee/from-api | jq .
```

Ожидаемый ответ: {"pairs":[...]} — в тесте было возвращено одна пара между employee 1 и 2.

Наблюдения и рекомендации
- Ранее наблюдались 400-ошибки и JSON-парс ошибки из-за некорректной отправки JSON из shell (вызовы вида `{algorithm_type:any}`). Всегда используйте кавычки и `-d @-`/файл.
- Data API ожидает заголовок `Authorization: Service <token>` — убедитесь, что `SERVICE_AUTH_TOKEN` установлен и одинаков в `web` и `matching-service` окружениях.
- Для production: храните секреты в Docker secrets, Vault или в CI/CD секретах. Временное хранение в `.env` допустимо, но с правами 600 и вне репозитория.

Дальше
- Могу добавить автоматический тест (smoke) в `tests/` или скрипт `scripts/e2e_smoke.sh` для повторяемости.
- Предлагаю настроить Docker secrets и обновить `docker/docker-compose.yml` и `docker/.env.example` — могу подготовить PR с инструкциями.

Дата: 2025-10-18
