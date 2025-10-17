# Article Scraper Container
# Python 3.11 with trafilatura + newspaper3k
# Created: 2025-10-09

FROM python:3.11-alpine

# Install system dependencies for lxml and newspaper3k
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    jpeg-dev \
    zlib-dev

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Default: Run continuous poller (for local overnight operation)
# Alternative: Run HTTP server with CMD ["python", "src/http_server.py"]
CMD ["python", "src/continuous_poller.py"]
