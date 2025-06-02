# 阶段1：构建镜像
FROM maven:3-openjdk-17-slim AS builder
RUN apt-get update && apt-get install -y git
COPY jacoco-settings.xml /app/jacoco-settings.xml
COPY pom.xml /app/pom.xml
WORKDIR /app

# 阶段2：运行时镜像
FROM maven:3-openjdk-17-slim
COPY --from=builder /app/jacoco-settings.xml /app/jacoco-settings.xml
COPY --from=builder /app/pom.xml /app/pom.xml
WORKDIR /app
CMD ["mvn", "clean", "verify", "-s", "/app/jacoco-settings.xml", "-f", "/app/pom.xml", "-Pcoverage-profile"]
