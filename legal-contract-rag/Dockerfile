# ==============================================================================
# Enterprise Legal Contract RAG & Assistant Platform — Primary Dockerfile
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# 1. Install system utilities and Microsoft SQL Server ODBC Driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg2 \
    unixodbc-dev \
    apt-transport-https \
    ca-certificates \
    && mkdir -p /usr/share/keyrings \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python application dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy application codebase and configuration
COPY backend/ /app/backend/
COPY resource/ /app/resource/
COPY config/ /app/config/
COPY shared-corpus/ /app/shared-corpus/
COPY scripts/ /app/scripts/
COPY tests/ /app/tests/
COPY run_capstone.py /app/run_capstone.py
COPY docs/ /app/docs/
COPY README.md .env.example /app/

# 4. Copy startup script and make executable
COPY backend/scripts/start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

EXPOSE 8000

CMD ["/app/start.sh"]

