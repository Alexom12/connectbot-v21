# Простая установка Maven для ConnectBot

Write-Host "Установка Apache Maven..." -ForegroundColor Green

# Параметры
$mavenVersion = "3.9.6" 
$mavenUrl = "https://archive.apache.org/dist/maven/maven-3/$mavenVersion/binaries/apache-maven-$mavenVersion-bin.zip"
$installDir = "C:\Tools\Maven"
$downloadPath = "$env:TEMP\maven.zip"

# Создаем директорию
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

# Проверяем, не установлен ли уже
if (Test-Path "$installDir\apache-maven-$mavenVersion\bin\mvn.cmd") {
    Write-Host "Maven уже установлен!" -ForegroundColor Green
    $mavenBin = "$installDir\apache-maven-$mavenVersion\bin"
    $env:PATH = "$env:PATH;$mavenBin"
    & "$mavenBin\mvn" --version
    exit 0
}

Write-Host "Скачивание Maven..." -ForegroundColor Yellow

# Скачиваем
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile($mavenUrl, $downloadPath)

Write-Host "Распаковка..." -ForegroundColor Yellow
Expand-Archive -Path $downloadPath -DestinationPath $installDir -Force

# Удаляем архив
Remove-Item $downloadPath -Force

# Настраиваем для текущей сессии
$mavenBin = "$installDir\apache-maven-$mavenVersion\bin"
$env:PATH = "$env:PATH;$mavenBin"
$env:MAVEN_HOME = "$installDir\apache-maven-$mavenVersion"

Write-Host "Maven установлен!" -ForegroundColor Green
& "$mavenBin\mvn" --version