# Simple start script without Redis
Write-Host "Starting ConnectBot Matching Service (no Redis)..." -ForegroundColor Green

# Set environment variables
$env:PATH = "$env:PATH;C:\Tools\Maven\apache-maven-3.9.6\bin"
$env:MAVEN_HOME = "C:\Tools\Maven\apache-maven-3.9.6"
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"

Write-Host "Compiling project..." -ForegroundColor Yellow
mvn clean compile -q

if ($LASTEXITCODE -eq 0) {
    Write-Host "Compilation successful" -ForegroundColor Green
    Write-Host "Starting service on http://localhost:8080..." -ForegroundColor Cyan
    Write-Host "Health Check: http://localhost:8080/api/matching/health" -ForegroundColor Cyan
    Write-Host "API Endpoints: http://localhost:8080/api/matching/algorithms" -ForegroundColor Cyan
    Write-Host ""
    
    # Start with no-redis profile
    mvn spring-boot:run -Dspring-boot.run.profiles=no-redis -DskipTests -q
}
else {
    Write-Host "Compilation error" -ForegroundColor Red
    exit 1
}