## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: build with Maven
FROM eclipse-temurin:21-jdk-jammy as builder

# Install Maven
ARG MAVEN_VERSION=3.9.6
ARG USER_HOME_DIR="/root"
ARG SHA=b9a31814a67b3a2dc3830333d233f531b2a5a8ac4032a8f5d8a21b52635a8a7c28a0c3b6b689282716f5a6f10134186f23c508e1f6103051820021a01b3b700b
ARG MAVEN_URL=https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz

RUN apt-get update && \
    apt-get install -y curl && \
    mkdir -p /usr/share/maven /usr/share/maven/ref && \
    curl -fsSL -o /tmp/apache-maven.tar.gz ${MAVEN_URL} && \
    echo "${SHA}  /tmp/apache-maven.tar.gz" | sha512sum -c - && \
    tar -xzf /tmp/apache-maven.tar.gz -C /usr/share/maven --strip-components=1 && \
    rm -f /tmp/apache-maven.tar.gz && \
    ln -s /usr/share/maven/bin/mvn /usr/bin/mvn

ENV MAVEN_HOME /usr/share/maven
ENV MAVEN_CONFIG "$USER_HOME_DIR/.m2"

WORKDIR /app
COPY . .

# Run the build using the installed Maven
RUN mvn -B -DskipTests=true -U clean package

# Stage 2: runtime image with minimal JRE
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=builder /app/target/matching-service-*.jar ./app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]