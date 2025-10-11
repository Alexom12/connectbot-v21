# Скрипт для установки Java 21 (Eclipse Temurin)
Write-Host "Начинаю установку Java 21 (Eclipse Temurin)..."

# URL для загрузки Eclipse Temurin 21 для Windows x64
$jdk21Url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_windows_hotspot_21.0.5_11.msi"
$downloadPath = "$env:TEMP\OpenJDK21.msi"

try {
    Write-Host "Загружаю JDK 21..."
    Invoke-WebRequest -Uri $jdk21Url -OutFile $downloadPath -UseBasicParsing
    
    Write-Host "Устанавливаю JDK 21..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $downloadPath, "/quiet", "/norestart" -Wait
    
    Write-Host "Установка завершена!"
    Write-Host "JDK 21 должен быть установлен в: C:\Program Files\Eclipse Adoptium\jdk-21.0.5.11-hotspot\"
    
    # Проверим установку
    $jdk21Path = "C:\Program Files\Eclipse Adoptium\jdk-21.0.5.11-hotspot\bin\java.exe"
    if (Test-Path $jdk21Path) {
        Write-Host "JDK 21 успешно установлен!"
        & $jdk21Path -version
    }
    else {
        Write-Host "Ошибка: JDK 21 не найден в ожидаемом месте"
    }
    
    # Удаляем временный файл
    Remove-Item $downloadPath -ErrorAction SilentlyContinue
    
}
catch {
    Write-Host "Ошибка при установке JDK 21: $($_.Exception.Message)"
    exit 1
}