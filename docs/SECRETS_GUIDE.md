# Secrets management guide (short)

Цель: предложить безопасные способы хранения и передачи секретов (например, `SERVICE_AUTH_TOKEN`, `SECRET_KEY`, `TELEGRAM_BOT_TOKEN`) для проекта `connectbot-v21`.

Опции (рекомендуемые)

1) Docker secrets (рекомендуется для production с Docker Swarm или Docker 20.10+ on Linux)
- Преимущества: секреты не попадают в переменные окружения контейнера в plain text, хранятся в docker swarm manager и монтируются внутрь контейнеров как защищённые файлы.
- Недостатки: требует Docker Swarm или docker-compose v2 с поддержкой secrets; на локальной Windows/Mac может быть неудобно.

2) HashiCorp Vault (рекомендуется для крупных инсталляций)
- Преимущества: централизованное управление секретами, ротация, политики доступа и audit.
- Недостатки: инфраструктурная сложность.

3) Защищённый `.env` (быстрый и простой)
- Преимущества: простота, работает везде.
- Недостатки: требует процедур защиты файла (`chmod 600`), нельзя хранить в репозитории.

Минимальный список секретов
- SERVICE_AUTH_TOKEN — токен для межсервисной аутентификации
- SECRET_KEY — Django SECRET_KEY
- TELEGRAM_BOT_TOKEN — токен бота
- DATABASE credentials (если используется внешняя БД)
- любые внешние API keys

Пример: Docker secrets (swarm)

1) Создать секреты на сервере (в каталоге проекта):

```bash
# в папке /opt/connectbot-v21
printf '%s' "${SERVICE_AUTH_TOKEN}" | docker secret create service_auth_token - || true
printf '%s' "${SECRET_KEY}" | docker secret create django_secret_key - || true
printf '%s' "${TELEGRAM_BOT_TOKEN}" | docker secret create telegram_bot_token - || true
```

2) Обновить `docker-compose.yml` (пример) — использовать `secrets:` и в сервисе `environment` ссылаться на файл внутри `/run/secrets/...`.

Пример-фрагмент для `matching-service`:

```yaml
services:
  matching-service:
    ...
    secrets:
      - service_auth_token

secrets:
  service_auth_token:
    external: true
```

В контейнере секрет будет доступен в `/run/secrets/service_auth_token`.

Пример: использование в `matching-service` (Spring Boot)
- Настроить `application.yml`/`application.properties` читать токен из файла, например:

```
# application.properties
matching.dataapi.service-token-file=/run/secrets/service_auth_token
```

И в старте приложения прочитать содержимое файла в конфиг и установить в `DATAAPI` client.

Альтернатива: mount secrets как env (compose v2 experimental) — менее безопасно.

Простой сценарий для `.env` (short-term)
- Создайте `.env` в корне (не в репозитории), на сервере: `chmod 600 .env`.
- Пример содержимого (`.env.example` уже присутствует) — заполните реальные токены и удалите `SERVICE_AUTH_TOKEN` из репозитория.

Автоматический скрипт (для локального/серверного использования)
- Я добавлю скрипт `scripts/create_secrets.sh`, который:
  - попросит ввести необходимые значения (или взять из окружения), создаст Docker secrets или заполнит защищённый `.env` по флагу.

Готовность
- Могу:
  - добавить `scripts/create_secrets.sh` в репозиторий и пример изменений `docker/docker-compose.yml` для использования secrets (два варианта: runtime `.env` и Docker secrets с `external: true`).
  - подготовить patch и PR в `main` с изменениями и инструкцией по развертыванию на сервере.

Что делаем дальше?
- Добавить скрипт и обновлённый `docker-compose.yml` с секцией `secrets` и инструкцией? (я выполню и запушу изменения).
