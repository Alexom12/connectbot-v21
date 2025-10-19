# Запускает сервис в Docker с hot-reload для разработки
echo "🚀 Starting development environment for matching-service..."

# Переходим в директорию проекта
cd "$(dirname "$0")/.."

# Запускаем Docker Compose
docker-compose -f docker-compose.dev.yml up --build -d

echo "✅ Service is running at http://localhost:8080"
echo "🔄 Hot-reload is enabled. Changes will be reflected automatically."
