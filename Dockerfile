FROM python:3.12-slim AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Node.js, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    ca-certificates \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY next-portal/package.json next-portal/package-lock.json* ./next-portal/
RUN cd next-portal && npm install

COPY . .

RUN cd next-portal && npm run build
RUN python train_model.py

COPY run_services.sh ./run_services.sh
RUN chmod +x ./run_services.sh

EXPOSE 3000 8080 8081

CMD ["./run_services.sh"]
