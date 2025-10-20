## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: build with Maven
FROM eclipse-temurin:21-jdk-jammy as builder

# Install Maven using apt-get, which is more reliable than manual download
RUN apt-get update && apt-get install -y maven

WORKDIR /app
COPY . .

# Run the build using the installed Maven
# The -DskipTests=true flag is used to speed up the build process
RUN mvn -B -DskipTests=true -U clean package

# Stage 2: runtime image with minimal JRE
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=builder /app/target/matching-service-*.jar ./app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]