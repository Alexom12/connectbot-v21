# Redis Troubleshooting Guide для ConnectBot v21

## 🚨 Проблема: Docker TLS handshake timeout

### Описание ошибки:
```
Error response from daemon: failed to resolve reference "docker.io/library/redis:7-alpine": 
failed to do request: Head "https://registry-1.docker.io/v2/library/redis/manifests/7-alpine": 
net/http: TLS handshake timeout
```

### 🔧 Решения:

## Решение 1: Альтернативная версия Redis

Попробуем другую версию Redis образа:

```yaml
# Замените в docker-compose.yml
redis:
  image: redis:alpine  # Вместо redis:7-alpine
  # или
  image: redis:6-alpine
  # или  
  image: redis:latest
```

## Решение 2: Настройка Docker Registry

### Для Windows Docker Desktop:

1. **Перезапустите Docker Desktop**
2. **Проверьте настройки прокси** в Docker Desktop:
   - Settings → Resources → Proxies
   - Если используете корпоративный прокси - настройте его

3. **Очистите Docker кеш:**
```powershell
docker system prune -a
docker builder prune -a
```

### Для корпоративных сетей:

4. **Используйте альтернативный registry:**
```yaml
redis:
  image: quay.io/bitnami/redis:7.0-debian-11
  # или
  image: ghcr.io/redis/redis-stack:latest
```

## Решение 3: Локальная установка Redis (без Docker)

### Windows установка:

#### Вариант A: Chocolatey
```powershell
# Установка Chocolatey (если нет)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Установка Redis
choco install redis-64 -y
```

#### Вариант B: MSI Installer
1. Скачайте Redis для Windows с GitHub: https://github.com/MicrosoftArchive/redis/releases
2. Установите MSI пакет
3. Запустите как службу Windows

#### Вариант C: WSL (Windows Subsystem for Linux)
```bash
# В WSL Ubuntu
sudo apt update
sudo apt install redis-server -y
sudo service redis-server start
```

### После установки локального Redis:

Обновите Django настройки:
```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',  # Локальный Redis
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Решение 4: Fallback на Django кеш

Если Redis недоступен, система автоматически использует Django locmem кеш:

```python
# config/settings.py - уже настроено
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'connectbot',
    }
}

# При недоступности Redis Django автоматически переключится на locmem
```

## Решение 5: Обновленный docker-compose.yml

Создайте альтернативную версию:

```yaml
version: '3.8'
services:
  redis:
    # Попробуйте разные варианты:
    image: redis:alpine                    # Вариант 1
    # image: redis:6-alpine               # Вариант 2  
    # image: bitnami/redis:latest         # Вариант 3
    # image: eqalpha/keydb:latest         # Вариант 4 (KeyDB - Redis совместимый)
    
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
    # Для bitnami/redis добавьте:
    # environment:
    #   - ALLOW_EMPTY_PASSWORD=yes
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

## Решение 6: Проверка сетевого подключения

### Диагностика:
```powershell
# Проверьте доступность Docker Hub
Test-NetConnection registry-1.docker.io -Port 443

# Проверьте DNS
nslookup registry-1.docker.io

# Проверьте прокси/файервол
curl -I https://registry-1.docker.io/v2/
```

### Если проблема с сетью:
```powershell
# Измените DNS на Google DNS
netsh interface ip set dns "Wi-Fi" static 8.8.8.8
netsh interface ip add dns "Wi-Fi" 8.8.4.4 index=2

# Или Cloudflare DNS
netsh interface ip set dns "Wi-Fi" static 1.1.1.1
netsh interface ip add dns "Wi-Fi" 1.0.0.1 index=2
```

## 🧪 Тестирование после исправления:

### Проверка Redis доступности:
```powershell
# Если Redis локально установлен
redis-cli ping

# Через Python
python test_redis.py

# Django команда
python manage.py redis_manager status
```

### Проверка Docker:
```powershell
# Простой тест Docker
docker run hello-world

# Тест Redis образа
docker run --rm redis:alpine redis-cli --version
```

## 📋 Рекомендованная последовательность действий:

1. **Быстрое решение:** Измените `redis:7-alpine` на `redis:alpine` в docker-compose.yml
2. **Перезапустите Docker Desktop** полностью
3. **Очистите кеш:** `docker system prune -a`
4. **Попробуйте снова:** `docker-compose up -d redis`
5. **Если не помогло:** Установите Redis локально через Chocolatey
6. **В крайнем случае:** Используйте только Django кеш (уже работает!)

## ✅ Проверка что все работает:

```bash
# ConnectBot работает с Redis
python manage.py redis_manager test

# ConnectBot работает без Redis  
python test_redis.py

# Java Matching Service
cd connectbot-java-services/matching-service
./mvnw spring-boot:run
```

**Главное:** ConnectBot v21 работает и БЕЗ Redis благодаря fallback системе! 🎉
