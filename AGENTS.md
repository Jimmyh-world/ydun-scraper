# Ydun Article Scraper

<!--
TEMPLATE_VERSION: 1.5.0
PROJECT: ydun-scraper
CREATED: 2025-10-17
-->

**Repository**: https://github.com/Jimmyh-world/ydun-scraper
**Purpose**: Article scraping microservice
**Type**: Stateless HTTP service
**Language**: Python 3.11

---

## Core Principles

1. **KISS** - Simple HTTP API, stateless design
2. **TDD** - Validate endpoints work
3. **SOC** - Single responsibility: scrape articles
4. **DRY** - Reuse extraction libraries
5. **Documentation** - Factual, dated
6. **Jimmy's Workflow** - RED/GREEN/CHECKPOINT
7. **YAGNI** - Only what's needed now
8. **Fix Now** - No deferred issues

---

## Service Overview

Python HTTP server that scrapes article content. Called by external services (Mundus Supabase edge function).

**Input**: URL via POST /scrape
**Output**: Article JSON (title, content, author, date)
**Deployment**: Docker container on Beast
**External Access**: https://ydun.kitt.agency

---

## Build & Test

```bash
# Local development
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/http_server.py

# Docker
docker build -t ydun-article-scraper:latest .
docker run -p 8080:8080 ydun-article-scraper:latest

# Test
curl http://localhost:8080/health
```

---

## Deployment

**Production**: Beast (192.168.68.100) via Docker Compose
**Repository**: network-infrastructure (references this repo)

---

**Last Updated**: 2025-10-17
