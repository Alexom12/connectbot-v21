# Spring Boot Matching Service Starter

Write-Host "ConnectBot Matching Service Starter" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

# Установка JAVA_HOME
$env:JAVA_HOME="C:\Program Files\Java\jdk-17"
Write-Host "JAVA_HOME set to: $env:JAVA_HOME" -ForegroundColor Cyan

# Переход в директорию
Set-Location "e:\ConnectBot v21\connectbot-java-services\matching-service"
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Cyan

# Сборка проекта
Write-Host "Building project..." -ForegroundColor Yellow
& .\mvnw.cmd clean compile -q

# Запуск сервиса
Write-Host "Starting Spring Boot service..." -ForegroundColor Yellow
Write-Host "URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Health: http://localhost:8080/api/matching/health" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray

& .\mvnw.cmd spring-boot:run