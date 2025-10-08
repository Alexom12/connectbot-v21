# PowerShell script for starting ConnectBot services

Write-Host "Starting ConnectBot services..." -ForegroundColor Green

# Check virtual environment exists
$venvPath = "E:\ConnectBot v21\venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found" -ForegroundColor Red
    Write-Host "Create virtual environment: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}
else {
    Write-Host "Activation script not found" -ForegroundColor Red
    exit 1
}

# Apply migrations
Write-Host "Applying migrations..." -ForegroundColor Yellow
python manage.py migrate

# Start Django server
Write-Host "Starting Django server..." -ForegroundColor Cyan
Start-Process python -ArgumentList "manage.py", "runserver" -NoNewWindow

# Start Telegram bot
Write-Host "Starting Telegram bot..." -ForegroundColor Cyan
Start-Process python -ArgumentList "manage.py", "runbot" -NoNewWindow

Write-Host "All services started!" -ForegroundColor Green
Write-Host "Django admin: http://localhost:8000/admin/" -ForegroundColor Gray
Write-Host "Bot is active and waiting for messages" -ForegroundColor Gray
