# Быстрый тест Spring Boot Matching Service

Write-Host "🧪 Testing ConnectBot Matching Service" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Тестовые данные
$testData = @(
    @{
        id = 1
        full_name = "Иван Иванов"
        position = "Разработчик"
        is_active = $true
    },
    @{
        id = 2
        full_name = "Мария Петрова"
        position = "Дизайнер"
        is_active = $true
    },
    @{
        id = 3
        full_name = "Алексей Сидоров"
        position = "Аналитик"
        is_active = $true
    },
    @{
        id = 4
        full_name = "Елена Козлова"
        position = "Менеджер"
        is_active = $true
    }
) | ConvertTo-Json

$baseUrl = "http://localhost:8080"

# Тест 1: Health Check
Write-Host "1. Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/matching/health" -UseBasicParsing
    Write-Host "✅ Health OK: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Health Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Тест 2: Algorithms List
Write-Host "`n2. Testing Algorithms List..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/matching/algorithms" -UseBasicParsing
    Write-Host "✅ Algorithms OK: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Algorithms Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Тест 3: Simple Matching
Write-Host "`n3. Testing Simple Matching..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/matching/coffee/simple" -Method POST -Body $testData -ContentType "application/json" -UseBasicParsing
    Write-Host "✅ Simple Matching OK: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Simple Matching Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Test Complete!" -ForegroundColor Green