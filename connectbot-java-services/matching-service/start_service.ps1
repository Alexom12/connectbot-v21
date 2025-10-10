# Spring Boot Matching Service Starter
# Проверяет Java и запускает микросервис

Write-Host "🚀 ConnectBot Matching Service Starter" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Проверка Java
Write-Host "📋 Проверка Java..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1
    Write-Host "✅ Java найдена:" -ForegroundColor Green  
    Write-Host $javaVersion[0] -ForegroundColor Cyan
}
catch {
    Write-Host "❌ Java не найдена! Установите Java 17+" -ForegroundColor Red
    exit 1
}

# Установка JAVA_HOME
$javaHome = "C:\Program Files\Java\jdk-17"
if (Test-Path $javaHome) {
    $env:JAVA_HOME = $javaHome
    Write-Host "✅ JAVA_HOME установлен: $javaHome" -ForegroundColor Green
}
else {
    Write-Host "⚠️ JAVA_HOME не найден, используем системную Java" -ForegroundColor Yellow
}

# Переход в директорию
Set-Location "e:\ConnectBot v21\connectbot-java-services\matching-service"
Write-Host "📂 Рабочая директория: $(Get-Location)" -ForegroundColor Cyan

# Проверка структуры проекта
if (-not (Test-Path "pom.xml")) {
    Write-Host "❌ pom.xml не найден!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "src/main/java")) {
    Write-Host "❌ Исходный код не найден!" -ForegroundColor Red
    exit 1  
}

Write-Host "✅ Структура проекта корректна" -ForegroundColor Green

# Сборка проекта
Write-Host "" 
Write-Host "🔨 Сборка проекта..." -ForegroundColor Yellow
try {
    & .\mvnw.cmd clean compile -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Проект собран успешно" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Ошибка сборки проекта" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Ошибка при запуске Maven: $_" -ForegroundColor Red
    exit 1
}

# Запуск сервиса  
Write-Host ""
Write-Host "🚀 Запуск Spring Boot сервиса..." -ForegroundColor Yellow
Write-Host "📡 URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🏥 Health: http://localhost:8080/api/matching/health" -ForegroundColor Cyan  
Write-Host "📚 API: http://localhost:8080/api/matching/algorithms" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Green

try {
    & .\mvnw.cmd spring-boot:run
}
catch {
    Write-Host "❌ Ошибка при запуске сервиса: $_" -ForegroundColor Red
    exit 1
}