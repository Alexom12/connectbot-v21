# Скрипт для загрузки портативной версии Java 21
Write-Host "Загружаю портативную версию Java 21..."

# URL для загрузки портативной версии OpenJDK 21
$jdk21ZipUrl = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_windows_hotspot_21.0.5_11.zip"
$downloadPath = "$env:TEMP\OpenJDK21.zip"
$installPath = "E:\ConnectBot v21\jdk-21"

try {
    Write-Host "Загружаю JDK 21 ZIP..."
    Invoke-WebRequest -Uri $jdk21ZipUrl -OutFile $downloadPath -UseBasicParsing
    
    Write-Host "Распаковываю в $installPath..."
    if (Test-Path $installPath) {
        Remove-Item $installPath -Recurse -Force
    }
    
    # Создаем папку для JDK
    New-Item -ItemType Directory -Path $installPath -Force
    
    # Распаковываем
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($downloadPath, $installPath)
    
    # Находим папку с JDK внутри распакованного архива
    $jdkFolder = Get-ChildItem $installPath | Where-Object { $_.PSIsContainer -and $_.Name -like "*jdk*" } | Select-Object -First 1
    
    if ($jdkFolder) {
        # Перемещаем содержимое из подпапки в основную папку
        $sourcePath = $jdkFolder.FullName
        $tempPath = "$installPath\temp"
        Move-Item $sourcePath $tempPath
        Get-ChildItem $tempPath | Move-Item -Destination $installPath
        Remove-Item $tempPath -Force
    }
    
    $javaExePath = "$installPath\bin\java.exe"
    if (Test-Path $javaExePath) {
        Write-Host "JDK 21 успешно установлен в: $installPath"
        & $javaExePath -version
        
        # Устанавливаем JAVA_HOME
        Write-Host "Устанавливаю JAVA_HOME в переменные окружения..."
        [Environment]::SetEnvironmentVariable("JAVA_HOME", $installPath, "User")
        $env:JAVA_HOME = $installPath
        
        Write-Host "JAVA_HOME установлен в: $installPath"
    } else {
        Write-Host "Ошибка: java.exe не найден"
    }
    
    # Удаляем временный файл
    Remove-Item $downloadPath -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "Ошибка: $($_.Exception.Message)"
    exit 1
}