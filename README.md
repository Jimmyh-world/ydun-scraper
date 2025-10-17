# Ydun Article Scraper

**Purpose**: Python-based article scraper microservice for Ydun Context Engine
**Created**: 2025-10-17
**Runtime**: Python 3.11
**Deployment**: Docker container

---

## Overview

Lightweight HTTP server that scrapes article content using trafilatura and newspaper3k. Designed to be called by Supabase edge functions or other external services.

**Architecture**: Stateless microservice - receives URL, returns scraped content.

---

## Quick Start

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run HTTP server
python src/http_server.py
```

Server runs on `http://localhost:8080`

### Docker Deployment

```bash
# Build image
docker build -t ydun-article-scraper:latest .

# Run container
docker run -d -p 8080:8080 --name ydun-scraper ydun-article-scraper:latest

# Health check
curl http://localhost:8080/health
```

---

## API Endpoints

### POST /scrape
Scrape article from URL

**Request:**
```json
{
  "url": "https://example.com/article",
  "method": "trafilatura"  // optional: "trafilatura" or "newspaper"
}
```

**Response:**
```json
{
  "success": true,
  "title": "Article Title",
  "content": "Article content...",
  "author": "Author Name",
  "publish_date": "2025-10-17",
  "url": "https://example.com/article"
}
```

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T10:00:00Z"
}
```

---

## Deployment

**Production:** Deployed on Beast (192.168.68.100) via Docker Compose
**External Access:** https://ydun.kitt.agency (via Cloudflare Tunnel)
**Called By:** Mundus Supabase edge function

---

## Development

**Language:** Python 3.11
**Dependencies:** trafilatura, newspaper3k, Flask
**Testing:** pytest (when needed)

---

**Last Updated:** 2025-10-17
