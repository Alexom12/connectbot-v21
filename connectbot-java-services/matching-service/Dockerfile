## Multi-stage Dockerfile for building and running the matching-service
# Stage 1: build with Maven
FROM eclipse-temurin:21-jdk-jammy as builder

# Install Maven
ARG MAVEN_VERSION=3.9.6
ARG USER_HOME_DIR="/root"
ARG SHA=e9f8715743438038333e385202110c767755324f053a6b5b351772157735214b1009b82332504653423539421be22725a5f5273ae63333a202024941155e047c
ARG BASE_URL=https://apache.osuosl.org/maven/maven-3/${MAVEN_VERSION}/binaries

RUN apt-get update && \
    apt-get install -y curl && \
    mkdir -p /usr/share/maven /usr/share/maven/ref && \
    curl -fsSL -o /tmp/apache-maven.tar.gz ${BASE_URL}/apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
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