# Ydun-Scraper Deployment Guide

**Updated:** 2025-10-17
**Environment:** Production (Gunicorn)
**Status:** Operational

---

## Overview

The ydun-scraper is deployed as a production-grade article extraction microservice. It uses Gunicorn as the WSGI server and is containerized with Docker for reliable deployment.

## Architecture

```
Client Request (HTTPS/HTTP)
    ↓
Cloudflare Tunnel (https://scrape.kitt.agency)
    ↓
Docker Container (port 5000 → 8080)
    ↓
Gunicorn Master (4 workers, gthread)
    ↓
Flask Application (http_server.py)
    ↓
trafilatura + newspaper3k (Article extraction)
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

**Location:** `/home/jimmyb/network-infrastructure/beast/docker/docker-compose.yml`

```bash
# Start scraper with other monitoring stack
cd ~/network-infrastructure/beast/docker
docker compose up -d ydun-scraper

# Verify running
docker compose ps

# View logs
docker compose logs -f ydun-scraper
```

**Configuration:**
- Build context: `/home/jimmyb/ydun-scraper`
- Port mapping: `5000:8080`
- Network: `monitoring` (shared with Prometheus, Grafana, etc.)
- Restart: `unless-stopped`

### Method 2: Direct Docker

```bash
# Build image
docker build -t ydun-scraper:latest /home/jimmyb/ydun-scraper

# Run container
docker run -d \
  --name ydun-scraper \
  -p 5000:8080 \
  ydun-scraper:latest \
  gunicorn --bind 0.0.0.0:8080 \
    --chdir /app/src \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    http_server:app

# Stop container
docker stop ydun-scraper
docker rm ydun-scraper
```

### Method 3: Local Development (Flask)

**For development only - not recommended for production:**

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
cd src
python http_server.py

# Runs on http://localhost:8080
```

**Note:** Flask development server shows warnings about production use. Use Gunicorn for any real usage.

## API Endpoint

### Health Check

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "service": "ydun-article-scraper",
  "status": "healthy"
}
```

### Article Extraction

```bash
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/article"]}'
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "stats": {
    "total": 1,
    "succeeded": 1,
    "failed": 0,
    "duration_seconds": 0.45
  }
}
```

See `MUNDUS-INTEGRATION.md` for complete API specification.

## Performance Configuration

### Default Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Workers | 4 | Adjust based on CPU cores |
| Threads/Worker | 2 | Good for I/O-bound tasks |
| Timeout | 120s | Allows complex page scraping |
| Max URLs/Request | 10 | Recommended batch size |

### Tuning for Different Environments

**2-Core System (e.g., small VPS):**
```bash
--workers 2 --threads 1
```

**8-Core System:**
```bash
--workers 8 --threads 2
```

**High-Memory Server (16+ GB):**
```bash
--workers 16 --threads 4 --max-requests 1000
```

### Memory Usage

- Base memory: ~200-300 MB
- Per worker overhead: ~50-100 MB
- Per active extraction: depends on article size
- Typical total: 500-800 MB with 4 workers

## Compliance Validation

### Compliance Controls

The service implements EU DSM Directive Article 4 compliance:

1. **robots.txt Compliance** - Respects crawl-delay and disallow rules
2. **TDM Opt-Out Detection** - Checks HTTP headers and meta tags
3. **User-Agent Identification** - Identifies as TDM bot
4. **Per-Domain Rate Limiting** - 1-2 second delays between requests
5. **Audit Trail Logging** - All compliance decisions logged

### Monitor Compliance Logs

```bash
# View compliance decisions
docker compose logs ydun-scraper | grep -E "TDM|robots|Rate limit"

# Expected output:
# INFO:article_extractor:robots.txt crawl-delay for example.com: 1.0s
# INFO:tdm_compliance:TDM ALLOWED: https://example.com - No opt-out signals detected
# INFO:batch_scraper:Rate limit: waiting 1.00s for example.com
```

### Validate Live Compliance

```bash
# Test with known news site
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.svd.se/nyheter/"]}'

# Check logs for compliance logs
docker compose logs ydun-scraper --tail 20 | grep -E "robots|TDM|Rate"
```

---

## Monitoring

### Docker Logs

```bash
# Real-time logs
docker compose logs -f ydun-scraper

# Last 100 lines
docker compose logs --tail 100 ydun-scraper

# Filter errors
docker compose logs ydun-scraper | grep ERROR
```

### Resource Usage

```bash
# CPU and memory
docker stats ydun-scraper

# More details
docker inspect ydun-scraper

# Process listing
docker top ydun-scraper
```

### Health Monitoring

```bash
# Check endpoint availability
while true; do
  curl -s http://localhost:5000/health | jq .
  sleep 10
done
```

## Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Run multiple containers on different ports
docker run -d -p 5001:8080 ydun-scraper:latest ...
docker run -d -p 5002:8080 ydun-scraper:latest ...
docker run -d -p 5003:8080 ydun-scraper:latest ...

# Use load balancer (nginx, HAProxy)
# Route requests across instances
```

### Vertical Scaling (More Workers)

Edit docker-compose.yml and increase `--workers`:

```yaml
command: gunicorn ... --workers 8 ...
```

Then restart:
```bash
docker compose up -d --build ydun-scraper
```

## Maintenance

### Regular Tasks

#### Daily
- Monitor error logs for exceptions
- Check resource usage
- Verify health endpoint responds

#### Weekly
- Review performance metrics
- Check for memory leaks
- Test batch processing

#### Monthly
- Update dependencies: `pip list --outdated`
- Review and optimize slow extractions
- Rotate logs if necessary

### Updates

```bash
# Rebuild image with updated dependencies
docker compose build --no-cache ydun-scraper

# Restart service
docker compose up -d ydun-scraper

# Verify new version
curl http://localhost:5000/health
```

## Troubleshooting

### "Worker (pid:X) exited with code 1"

**Cause:** Worker crashed during request

**Solution:**
```bash
# Check logs for specific error
docker compose logs ydun-scraper | tail -50

# Common fixes:
# 1. Increase timeout if requests are slow
# 2. Check target websites are accessible
# 3. Restart container
docker compose restart ydun-scraper
```

### High Memory Usage

**Cause:** Extracting very large HTML files

**Solution:**
```bash
# Monitor which URLs cause issues
docker compose logs ydun-scraper | grep "processing"

# Increase container memory limit
# (in docker-compose.yml)
mem_limit: '2g'

# Restart
docker compose up -d ydun-scraper
```

### Slow Extraction (>30 seconds)

**Cause:** Complex website or network issues

**Solution:**
```bash
# Test URL directly
curl -s "https://example.com/article" | wc -c  # Check size

# Check network connectivity
ping -c 1 example.com

# Monitor from container
docker exec ydun-scraper curl -v https://example.com/article

# Consider timeout or retry logic
```

### Connection Refused on Port 5000

**Cause:** Container not running or port in use

**Solution:**
```bash
# Check if container is running
docker compose ps

# If not running, start it
docker compose up -d ydun-scraper

# If port is in use
lsof -i :5000

# Kill other process using port
kill -9 <PID>
```

## Dependencies

### Python Packages

- **flask** - Web framework
- **gunicorn** - Production WSGI server
- **trafilatura** - Primary article extraction
- **newspaper3k** - Fallback extraction
- **lxml** - HTML parsing
- **requests** - HTTP client

### System Dependencies (Alpine Linux)

```dockerfile
RUN apk add --no-cache \
    gcc musl-dev \
    libxml2-dev libxslt-dev \
    jpeg-dev zlib-dev
```

## Security

### Network Access

- **Internal:** Only accessible within `monitoring` network
- **External:** Via Cloudflare Tunnel (HTTPS encrypted)
- **No authentication:** Currently open (add if needed)

### Input Validation

- URLs validated before processing
- Invalid URLs rejected gracefully
- Batch size limited to 10 URLs

### Resource Limits

- Request timeout: 120 seconds
- Max workers: 4 (configurable)
- Memory limit: Docker container limit

## Deployment Checklist

- [x] Python 3.11 base image (Alpine)
- [x] Dependencies installed in requirements.txt
- [x] Gunicorn configured for production
- [x] Flask app working correctly
- [x] Docker image builds successfully
- [x] Container runs and is healthy
- [x] Port mapping configured (5000:8080)
- [x] Network connectivity verified
- [x] Logging configured
- [x] Restart policy set
- [x] Documentation complete

## Integration

### Mundus Integration

See `/home/jimmyb/network-infrastructure/beast/docs/MUNDUS-INTEGRATION.md` for:
- Complete API specification
- Supabase edge function examples
- Integration patterns (real-time, bulk, retry)
- Testing procedures

### External Access

Via Cloudflare Tunnel: `https://scrape.kitt.agency/scrape`

See `/home/jimmyb/network-infrastructure/beast/cloudflare/TUNNEL-HOST-DEPLOYMENT.md`

## References

- **Dockerfile:** `/home/jimmyb/ydun-scraper/Dockerfile`
- **HTTP Server:** `/home/jimmyb/ydun-scraper/src/http_server.py`
- **Requirements:** `/home/jimmyb/ydun-scraper/requirements.txt`
- **Gunicorn Docs:** https://docs.gunicorn.org/
- **Trafilatura Docs:** https://trafilatura.readthedocs.io/

---

**Last Updated:** 2025-10-17
**Deployment Status:** ✅ Production Ready
**Deployed On:** Docker + Gunicorn
**External URL:** https://scrape.kitt.agency
