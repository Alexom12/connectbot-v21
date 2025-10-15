## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: build with Maven
FROM maven:3.9.4-eclipse-temurin-21 as builder
WORKDIR /workspace

# Copy maven wrapper and settings first to take advantage of layer caching
COPY mvnw mvnw
COPY .mvn .mvn
COPY pom.xml pom.xml

# Download dependencies
RUN ./mvnw -B -q dependency:go-offline -DskipTests

# Copy the rest of the sources and build
COPY src src
RUN ./mvnw -B -q -DskipTests package

# Stage 2: runtime image with minimal JRE
FROM eclipse-temurin:21-jre as runtime
WORKDIR /app

# Copy jar built in the previous stage
COPY --from=builder /workspace/target/*.jar ./matching-service.jar

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "/app/matching-service.jar", "--server.port=8081"]
# Используем официальный образ OpenJDK 17 как базовый
FROM openjdk:17-jdk-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы Maven для кеширования зависимостей
COPY pom.xml .
COPY mvnw .
COPY .mvn .mvn

# Загружаем зависимости (будет закешировано если pom.xml не изменился)
RUN ./mvnw dependency:go-offline -B

# Копируем исходный код
COPY src src

# Собираем приложение
RUN ./mvnw clean package -DskipTests

# Создаем пользователя для безопасности
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Переключаемся на созданного пользователя
USER appuser

# Открываем порт 8080
EXPOSE 8080

# Запускаем приложение
ENTRYPOINT ["java", "-jar", "target/matching-service-1.0.0.jar"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/matching/health || exit 1