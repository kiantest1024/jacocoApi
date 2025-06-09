FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    maven \
    openjdk-11-jdk \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

RUN useradd -m -s /bin/bash jacoco

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY start.py .
COPY src/ src/
COPY config/ config/
COPY static/ static/
COPY docker/ docker/

RUN mkdir -p reports logs && \
    chown -R jacoco:jacoco /app

RUN pip3 install --no-cache-dir -r requirements.txt

USER jacoco

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["python3", "start.py"]
