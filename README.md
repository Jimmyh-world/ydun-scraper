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

## Legal Compliance

**Framework:** EU DSM Directive Article 4 (Text and Data Mining)

The scraper implements comprehensive compliance controls for lawful TDM operations:

### Implemented Controls

1. **robots.txt Compliance**
   - Respects crawl-delay directives from target websites
   - Honors disallow rules
   - Identifies as `YdunScraperBot/1.0`

2. **TDMRep Opt-Out Detection**
   - Checks HTTP headers (`X-TDM-Opt-Out`, `TDM-Reservation`)
   - Detects HTML meta tags (`tdm-reservation`, robots `noai`)
   - Blocks scraping on opt-out signals

3. **Per-Domain Rate Limiting**
   - Reduced concurrency to 3 (from 10)
   - Enforces minimum 1-2 second delays between requests
   - Respects robots.txt crawl-delay

4. **Audit Trail Logging**
   - All compliance decisions logged
   - Full audit trail for GDPR compliance
   - TDM allowed/blocked decisions recorded

**Status:** ✅ Fully Compliant (2025-10-19)

See `COMPLIANCE.md` for detailed framework documentation.

---

## Deployment

**Production:** Deployed on Beast (192.168.68.100) via Docker Compose
**External Access:** https://ydun.kitt.agency (via Cloudflare Tunnel)
**Called By:** Mundus Supabase edge function

See `DEPLOYMENT.md` for detailed deployment instructions.

---

## Development

**Language:** Python 3.11
**Dependencies:** trafilatura, newspaper3k, Flask, beautifulsoup4
**Testing:** pytest (when needed)
**Compliance:** Full EU DSM Directive Article 4 compliance

---

## Documentation

- `COMPLIANCE.md` - Legal compliance framework (EU DSM Directive Article 4)
- `DEPLOYMENT.md` - Deployment guide and troubleshooting
- `LIVE_TESTING_RESULTS.md` - Testing results and performance metrics

---

**Last Updated:** 2025-10-19
**Status:** ✅ Production Ready - Legal Compliant
