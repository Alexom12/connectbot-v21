## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: Build with official Maven image, which is more reliable
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY . .
# The -DskipTests=true flag is used to speed up the build process
RUN mvn -B -DskipTests=true clean package

# Stage 2: Create the final runtime image
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=builder /app/target/matching-service-*.jar ./app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]