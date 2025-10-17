## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: build with Maven
FROM maven:3.9.4-eclipse-temurin-21 as builder
WORKDIR /workspace

# Copy pom and sources
COPY pom.xml ./
COPY .mvn .mvn
COPY src ./src
COPY mvnw ./

# Download dependencies and build
RUN chmod +x mvnw \
    && ./mvnw dependency:go-offline -B
RUN mvn -B -q -DskipTests package

# Stage 2: runtime image with minimal JRE
FROM eclipse-temurin:21-jre
WORKDIR /app

# Copy jar built in the previous stage
COPY --from=builder /workspace/target/*.jar ./matching-service.jar

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "./matching-service.jar", "--server.port=8081"]

# Optional healthcheck (adjust path if controller exposes different endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8081/actuator/health || exit 1