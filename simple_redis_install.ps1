# ConnectBot v21 - Простая установка Redis для Windows
# Автор: ConnectBot Team
# Дата: 9 октября 2025

param(
    [switch]$CheckOnly,
    [switch]$Uninstall,
    [string]$Method = "Auto"
)

Write-Host "🔥 ConnectBot v21 - Redis Installation Helper" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

function Test-AdminPrivileges {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-RedisInstalled {
    Write-Host "🔍 Проверка установки Redis..." -ForegroundColor Yellow
    
    # Проверка через redis-cli
    try {
        $version = redis-cli --version 2>$null
        if ($version) {
            Write-Host "✅ Redis найден: $version" -ForegroundColor Green
            return $true
        }
    }
    catch {}
    
    # Проверка службы Windows
    $service = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "✅ Redis служба найдена: $($service.Status)" -ForegroundColor Green
        return $true
    }
    
    # Проверка Chocolatey пакета
    try {
        $chocoList = choco list --local-only redis 2>$null
        if ($chocoList -match "redis") {
            Write-Host "✅ Redis установлен через Chocolatey" -ForegroundColor Green
            return $true
        }
    }
    catch {}
    
    Write-Host "❌ Redis не найден" -ForegroundColor Red
    return $false
}

function Test-ChocolateyInstalled {
    try {
        $chocoVersion = choco --version 2>$null
        if ($chocoVersion) {
            Write-Host "✅ Chocolatey найден: $chocoVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {}
    
    Write-Host "❌ Chocolatey не установлен" -ForegroundColor Red
    return $false
}

function Install-Chocolatey {
    Write-Host "📦 Установка Chocolatey..." -ForegroundColor Yellow
    
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Обновляем PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        
        Write-Host "✅ Chocolatey установлен успешно!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Ошибка установки Chocolatey: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Install-RedisChocolatey {
    Write-Host "🍫 Установка Redis через Chocolatey..." -ForegroundColor Yellow
    
    try {
        choco install redis-64 -y
        Write-Host "✅ Redis установлен через Chocolatey!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Ошибка установки Redis: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Install-RedisWSL {
    Write-Host "🐧 Установка Redis через WSL..." -ForegroundColor Yellow
    
    # Проверяем наличие WSL
    try {
        $wslVersion = wsl --version 2>$null
        if (-not $wslVersion) {
            Write-Host "❌ WSL не найден. Установите WSL сначала." -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ WSL не доступен" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Установка Redis в WSL Ubuntu..." -ForegroundColor Cyan
    
    try {
        wsl sudo apt update
        wsl sudo apt install redis-server -y
        wsl sudo service redis-server start
        
        Write-Host "✅ Redis установлен в WSL!" -ForegroundColor Green
        Write-Host "💡 Для запуска используйте: wsl sudo service redis-server start" -ForegroundColor Cyan
        return $true
    }
    catch {
        Write-Host "❌ Ошибка установки Redis в WSL: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Start-RedisService {
    Write-Host "🚀 Запуск Redis..." -ForegroundColor Yellow
    
    # Пробуем запустить службу Windows
    try {
        $service = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
        if ($service) {
            if ($service.Status -ne "Running") {
                Start-Service -Name "Redis"
                Write-Host "✅ Redis служба запущена" -ForegroundColor Green
            }
            else {
                Write-Host "✅ Redis служба уже запущена" -ForegroundColor Green
            }
            return $true
        }
    }
    catch {}
    
    # Пробуем WSL
    try {
        wsl sudo service redis-server start 2>$null
        Write-Host "✅ Redis запущен в WSL" -ForegroundColor Green
        return $true
    }
    catch {}
    
    Write-Host "⚠️  Не удалось запустить Redis автоматически" -ForegroundColor Yellow
    Write-Host "💡 Попробуйте запустить вручную: redis-server" -ForegroundColor Cyan
    return $false
}

function Test-RedisConnection {
    Write-Host "🔗 Тестирование подключения к Redis..." -ForegroundColor Yellow
    
    try {
        $ping = redis-cli ping 2>$null
        if ($ping -eq "PONG") {
            Write-Host "✅ Redis отвечает на ping!" -ForegroundColor Green
            return $true
        }
    }
    catch {}
    
    # Пробуем WSL
    try {
        $wslPing = wsl redis-cli ping 2>$null
        if ($wslPing -eq "PONG") {
            Write-Host "✅ Redis в WSL отвечает на ping!" -ForegroundColor Green
            Write-Host "💡 Используйте WSL Redis: wsl redis-cli" -ForegroundColor Cyan
            return $true
        }
    }
    catch {}
    
    Write-Host "❌ Redis не отвечает" -ForegroundColor Red
    return $false
}

function Uninstall-Redis {
    Write-Host "🗑️  Удаление Redis..." -ForegroundColor Yellow
    
    # Остановка службы
    try {
        Stop-Service -Name "Redis" -ErrorAction SilentlyContinue
        Write-Host "⏹️  Redis служба остановлена" -ForegroundColor Yellow
    }
    catch {}
    
    # Удаление через Chocolatey
    try {
        choco uninstall redis-64 -y 2>$null
        Write-Host "✅ Redis удален через Chocolatey" -ForegroundColor Green
    }
    catch {}
    
    Write-Host "✅ Redis удален" -ForegroundColor Green
}

function Show-Usage {
    Write-Host ""
    Write-Host "📋 Использование:" -ForegroundColor Cyan
    Write-Host "  .\simple_redis_install.ps1                    # Автоматическая установка"
    Write-Host "  .\simple_redis_install.ps1 -CheckOnly        # Только проверка"
    Write-Host "  .\simple_redis_install.ps1 -Method Chocolatey # Принудительно через Chocolatey"
    Write-Host "  .\simple_redis_install.ps1 -Method WSL        # Принудительно через WSL"
    Write-Host "  .\simple_redis_install.ps1 -Uninstall        # Удаление Redis"
    Write-Host ""
}

# =============================================================================
# Главная логика
# =============================================================================

# Проверка только
if ($CheckOnly) {
    $redisInstalled = Test-RedisInstalled
    if ($redisInstalled) {
        $connected = Test-RedisConnection
        if ($connected) {
            Write-Host "🎉 Redis готов к использованию!" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Redis установлен, но не запущен" -ForegroundColor Yellow
        }
    }
    Show-Usage
    exit 0
}

# Удаление
if ($Uninstall) {
    Uninstall-Redis
    exit 0
}

# Установка
Write-Host ""

# Проверяем права админа
if (-not (Test-AdminPrivileges)) {
    Write-Host "⚠️  Рекомендуется запустить с правами администратора" -ForegroundColor Yellow
    Write-Host "💡 Нажмите любую клавишу для продолжения или Ctrl+C для отмены..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Проверяем текущую установку
if (Test-RedisInstalled) {
    Write-Host "✅ Redis уже установлен!" -ForegroundColor Green
    
    if (Test-RedisConnection) {
        Write-Host "🎉 Redis готов к использованию!" -ForegroundColor Green
    }
    else {
        Write-Host "🚀 Пытаемся запустить Redis..." -ForegroundColor Yellow
        Start-RedisService
        Start-Sleep -Seconds 3
        Test-RedisConnection
    }
    
    exit 0
}

# Выбираем метод установки
$installMethod = $Method

if ($installMethod -eq "Auto") {
    Write-Host "🤖 Автоматический выбор метода установки..." -ForegroundColor Cyan
    
    if (Test-ChocolateyInstalled) {
        $installMethod = "Chocolatey"
    }
    else {
        # Проверяем WSL
        try {
            $wslCheck = wsl --version 2>$null
            if ($wslCheck) {
                $installMethod = "WSL"
            }
            else {
                $installMethod = "Chocolatey"  # Установим Chocolatey если WSL нет
            }
        }
        catch {
            $installMethod = "Chocolatey"
        }
    }
}

Write-Host "📋 Выбран метод: $installMethod" -ForegroundColor Cyan

# Устанавливаем Redis
$success = $false

switch ($installMethod) {
    "Chocolatey" {
        if (-not (Test-ChocolateyInstalled)) {
            $chocoInstalled = Install-Chocolatey
            if (-not $chocoInstalled) {
                Write-Host "❌ Не удалось установить Chocolatey" -ForegroundColor Red
                break
            }
        }
        $success = Install-RedisChocolatey
    }
    
    "WSL" {
        $success = Install-RedisWSL
    }
    
    default {
        Write-Host "❌ Неизвестный метод: $installMethod" -ForegroundColor Red
        Show-Usage
        exit 1
    }
}

if ($success) {
    Write-Host ""
    Write-Host "🎉 Redis установлен успешно!" -ForegroundColor Green
    
    # Пытаемся запустить
    Start-RedisService
    Start-Sleep -Seconds 5
    
    # Тестируем подключение
    if (Test-RedisConnection) {
        Write-Host ""
        Write-Host "✅ Установка завершена! Redis готов к использованию." -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 Следующие шаги:" -ForegroundColor Cyan
        Write-Host "  1. Проверьте ConnectBot: python test_redis.py" 
        Write-Host "  2. Запустите бот: python manage.py runbot"
        Write-Host "  3. Запустите Java сервис: cd connectbot-java-services/matching-service && ./mvnw spring-boot:run"
    }
    else {
        Write-Host ""
        Write-Host "⚠️  Redis установлен, но не отвечает на подключения" -ForegroundColor Yellow
        Write-Host "💡 Попробуйте перезапустить скрипт или запустить Redis вручную" -ForegroundColor Cyan
    }
}
else {
    Write-Host ""
    Write-Host "❌ Установка не удалась" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Альтернативные варианты:" -ForegroundColor Cyan
    Write-Host "  1. Скачайте Redis MSI: https://github.com/MicrosoftArchive/redis/releases"
    Write-Host "  2. Используйте Docker (если доступен): docker run -d -p 6379:6379 redis:alpine"
    Write-Host "  3. ConnectBot работает и БЕЗ Redis! Просто запустите: python manage.py runbot"
}

Write-Host ""
