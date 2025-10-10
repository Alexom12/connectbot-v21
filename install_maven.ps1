# Быстрая установка Maven для ConnectBot
# Скачивает и устанавливает Maven 3.9.6

Write-Host "📦 Установка Apache Maven..." -ForegroundColor Green

# Параметры
$mavenVersion = "3.9.6"
$mavenUrl = "https://archive.apache.org/dist/maven/maven-3/$mavenVersion/binaries/apache-maven-$mavenVersion-bin.zip"
$installDir = "C:\Tools\Maven"
$downloadPath = "$env:TEMP\maven.zip"

# Создаем директорию
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Write-Host "✅ Создана директория: $installDir" -ForegroundColor Green
}

# Проверяем, не установлен ли уже
if (Test-Path "$installDir\apache-maven-$mavenVersion\bin\mvn.cmd") {
    Write-Host "✅ Maven уже установлен в: $installDir\apache-maven-$mavenVersion" -ForegroundColor Green
    
    # Добавляем в PATH если нет
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $mavenBin = "$installDir\apache-maven-$mavenVersion\bin"
    
    if ($currentPath -notlike "*$mavenBin*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$mavenBin", "User")
        $env:PATH = "$env:PATH;$mavenBin"
        Write-Host "✅ Maven добавлен в PATH" -ForegroundColor Green
    }
    
    # Устанавливаем MAVEN_HOME
    [Environment]::SetEnvironmentVariable("MAVEN_HOME", "$installDir\apache-maven-$mavenVersion", "User") 
    $env:MAVEN_HOME = "$installDir\apache-maven-$mavenVersion"
    Write-Host "✅ MAVEN_HOME установлен" -ForegroundColor Green
    
    Write-Host "🚀 Maven готов к использованию!" -ForegroundColor Green
    & "$mavenBin\mvn" --version
    exit 0
}

Write-Host "📥 Скачивание Maven $mavenVersion..." -ForegroundColor Yellow

try {
    # Скачиваем
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($mavenUrl, $downloadPath)
    Write-Host "✅ Maven скачан" -ForegroundColor Green
    
    # Распаковываем
    Write-Host "📂 Распаковка Maven..." -ForegroundColor Yellow
    Expand-Archive -Path $downloadPath -DestinationPath $installDir -Force
    Write-Host "✅ Maven распакован" -ForegroundColor Green
    
    # Удаляем архив
    Remove-Item $downloadPath -Force
    
    # Настраиваем переменные среды
    $mavenBin = "$installDir\apache-maven-$mavenVersion\bin"
    $mavenHome = "$installDir\apache-maven-$mavenVersion"
    
    # PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$mavenBin*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$mavenBin", "User")
        $env:PATH = "$env:PATH;$mavenBin"
        Write-Host "✅ Maven добавлен в PATH" -ForegroundColor Green
    }
    
    # MAVEN_HOME
    [Environment]::SetEnvironmentVariable("MAVEN_HOME", $mavenHome, "User")
    $env:MAVEN_HOME = $mavenHome
    Write-Host "✅ MAVEN_HOME установлен: $mavenHome" -ForegroundColor Green
    
    Write-Host "🎉 Maven успешно установлен!" -ForegroundColor Green
    Write-Host "Версия:" -ForegroundColor Cyan
    & "$mavenBin\mvn" --version
    
}
catch {
    Write-Host "❌ Ошибка установки Maven: $_" -ForegroundColor Red
    exit 1
}