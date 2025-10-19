# Week 1: Legal Compliance Implementation - Execution Spec for Beast

**Created:** 2025-10-19
**Orchestrator:** Chromebook
**Executor:** Beast (Haiku 4.5 Specialist)
**Project:** ydun-scraper
**Priority:** 🔴 CRITICAL (Legal compliance required before scaling)

---

## Executive Summary

**Objective:** Implement TDM legal compliance and robots.txt respect to eliminate legal exposure and reduce site blocking.

**Background:** Live testing (2025-10-18) identified 5 critical issues. This spec addresses Week 1 priorities: legal compliance and robots.txt respect.

**Expected Outcome:**
- ✅ robots.txt parsing and crawl-delay respect
- ✅ TDMRep opt-out detection
- ✅ Proper User-Agent identification
- ✅ Per-domain rate limiting (1-2 req/sec)
- ✅ 187 disconnections → <20 (90% reduction expected)
- ✅ Legal compliance with EU DSM Directive Article 4

**Timeline:** Week 1 (4-6 hours implementation + testing)

---

## Context Documents (Read First)

**Before starting, read these files:**
1. `/home/jamesb/ydun-scraper/LIVE_TESTING_RESULTS.md` - Issues identified
2. `/home/jamesb/ydun-scraper/AGENTS.md` - Project guidelines
3. `/home/jamesb/ydun-scraper/DEPLOYMENT.md` - Current deployment
4. This spec (WEEK-1-LEGAL-COMPLIANCE-SPEC.md)

**Current Service Status:**
- Deployed: https://scrape.kitt.agency
- Docker container: ydun-scraper:latest
- Location: Beast (192.168.68.100)
- Status: ✅ Operational but non-compliant

---

## Implementation Plan (Jimmy's Workflow)

Follow RED→GREEN→CHECKPOINT for each component.

---

## Component 1: robots.txt Compliance

### 🔴 RED: Implementation

**File:** `src/article_extractor.py`

**Changes Required:**

1. **Enable robots.txt in trafilatura (line ~99):**
```python
# OLD:
downloaded = trafilatura.fetch_url(url)

# NEW:
downloaded = trafilatura.fetch_url(url, respect_robots_txt=True)
```

2. **Add fallback for newspaper3k (line ~150):**
```python
# Add before newspaper3k extraction
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def check_robots_txt(url):
    """Check if URL is allowed by robots.txt"""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{domain}/robots.txt"

    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
        return parser.can_fetch("YdunScraperBot/1.0", url)
    except:
        # If robots.txt unavailable, allow (fail open)
        return True

# Before newspaper3k extraction:
if not check_robots_txt(url):
    logger.warning(f"robots.txt disallows scraping: {url}")
    return None
```

3. **Add crawl-delay parsing:**
```python
def get_crawl_delay(url):
    """Get crawl-delay from robots.txt"""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{domain}/robots.txt"

    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
        delay = parser.crawl_delay("YdunScraperBot/1.0")
        return delay if delay else 1.0  # Default 1 second
    except:
        return 1.0  # Default 1 second if unavailable
```

### 🟢 GREEN: Validation

**Test Commands:**
```bash
# Unit test for robots.txt checking
pytest tests/test_robots_compliance.py -v

# Test with known robots.txt sites
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.expressen.se/nyheter/"]}'

# Expected: Should log crawl-delay and respect it

# Test with disallowed URL
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.google.com/search?q=test"]}'

# Expected: Should reject or skip (Google blocks scrapers in robots.txt)
```

**Validation Criteria:**
- [ ] trafilatura respects robots.txt
- [ ] newspaper3k fallback checks robots.txt
- [ ] Crawl-delay is parsed and logged
- [ ] Disallowed URLs are skipped with warning log
- [ ] No regression in successful extractions

### 🔵 CHECKPOINT

**Deliverables:**
- Updated `article_extractor.py` with robots.txt compliance
- Unit tests passing
- Manual validation complete

**Rollback Procedure:**
```bash
git revert <commit-hash>
docker compose restart ydun-scraper
# Time to rollback: 2 minutes
```

---

## Component 2: TDMRep Opt-Out Detection

### 🔴 RED: Implementation

**File:** Create new `src/tdm_compliance.py`

**TDMRep Detection (W3C Standard):**
```python
"""TDM (Text and Data Mining) compliance module"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def check_tdm_optout(url, html_content=None):
    """
    Check for TDM opt-out signals per W3C TDMRep standard

    Returns: (allowed: bool, reason: str)
    """
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Check HTTP headers
    try:
        response = requests.head(url, timeout=5)
        if 'X-TDM-Opt-Out' in response.headers:
            return False, "HTTP header: X-TDM-Opt-Out present"
        if 'TDM-Reservation' in response.headers:
            return False, f"HTTP header: TDM-Reservation = {response.headers['TDM-Reservation']}"
    except:
        pass  # Continue checking other signals

    # 2. Check HTML meta tags (if content provided)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for TDMRep meta tag
        tdm_meta = soup.find('meta', attrs={'name': 'tdm-reservation'})
        if tdm_meta and tdm_meta.get('content') == '1':
            return False, "HTML meta: tdm-reservation = 1"

        # Check for AI training opt-out (common pattern)
        ai_meta = soup.find('meta', attrs={'name': 'robots'})
        if ai_meta:
            content = ai_meta.get('content', '').lower()
            if 'noai' in content or 'noimageai' in content:
                return False, f"HTML meta robots: {content}"

    # 3. Check robots.txt for TDM-specific directives
    # (Already handled in Component 1)

    return True, "No opt-out signals detected"

def log_tdm_decision(url, allowed, reason):
    """Log TDM compliance decision for audit trail"""
    if allowed:
        logger.info(f"TDM ALLOWED: {url} - {reason}")
    else:
        logger.warning(f"TDM BLOCKED: {url} - {reason}")

    # TODO: Consider writing to compliance log file or database
    # for audit trail (GDPR requirement)
```

**Integrate into `article_extractor.py`:**
```python
from tdm_compliance import check_tdm_optout, log_tdm_decision

def extract_article(url):
    """Extract article content with TDM compliance"""

    # 1. Check robots.txt (Component 1)
    if not check_robots_txt(url):
        logger.warning(f"robots.txt disallows: {url}")
        return None

    # 2. Fetch content
    downloaded = trafilatura.fetch_url(url, respect_robots_txt=True)

    # 3. Check TDM opt-out signals
    allowed, reason = check_tdm_optout(url, downloaded)
    log_tdm_decision(url, allowed, reason)

    if not allowed:
        return None

    # 4. Extract if allowed
    extracted = trafilatura.extract(downloaded, ...)
    return extracted
```

### 🟢 GREEN: Validation

**Test Commands:**
```bash
# Unit test TDM detection
pytest tests/test_tdm_compliance.py -v

# Test with site that has TDM opt-out (if known)
# Test with site that allows TDM
# Verify logging is working

# Check compliance log
docker logs ydun-scraper | grep "TDM ALLOWED\|TDM BLOCKED"

# Expected: Clear audit trail of TDM decisions
```

**Validation Criteria:**
- [ ] TDMRep meta tags detected
- [ ] HTTP headers checked
- [ ] Opt-out URLs are skipped
- [ ] Allowed URLs proceed to extraction
- [ ] All decisions logged (audit trail)
- [ ] No false positives (legitimate content blocked)

### 🔵 CHECKPOINT

**Deliverables:**
- New `tdm_compliance.py` module
- Integration in `article_extractor.py`
- Unit tests passing
- Audit trail logging functional

**Rollback Procedure:**
```bash
git revert <commit-hash>
docker compose restart ydun-scraper
# Time to rollback: 2 minutes
```

---

## Component 3: User-Agent & Rate Limiting

### 🔴 RED: Implementation

**File:** `src/batch_scraper.py` and `config.py`

**Changes Required:**

1. **Update User-Agent (config.py or batch_scraper.py):**
```python
# OLD (likely default or browser-like):
# requests.get(url)

# NEW (identify as TDM bot):
HEADERS = {
    'User-Agent': 'YdunScraperBot/1.0 (+https://kitt.agency/bot; TDM for news summarization; contact@kitt.agency)'
}

requests.get(url, headers=HEADERS)
```

**Format follows RFC 9309 (Robots Exclusion Protocol):**
- Bot name and version
- Contact info or policy URL
- Purpose statement

2. **Reduce concurrency (batch_scraper.py line ~50):**
```python
# OLD:
max_concurrent = 10

# NEW:
max_concurrent = 3  # Safer starting point

# TODO: Make this configurable per domain
# Some domains may allow higher, others require 1
```

3. **Add per-domain rate limiting:**
```python
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

class DomainRateLimiter:
    """Enforce per-domain rate limits from robots.txt"""

    def __init__(self):
        self.last_request = defaultdict(lambda: datetime.min)
        self.delays = {}  # domain -> crawl_delay seconds

    def get_delay(self, domain):
        """Get required delay for domain (from robots.txt or default)"""
        return self.delays.get(domain, 1.0)  # Default 1 second

    async def wait_if_needed(self, domain):
        """Wait if we need to respect crawl-delay"""
        required_delay = self.get_delay(domain)
        last_req = self.last_request[domain]
        elapsed = (datetime.now() - last_req).total_seconds()

        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.info(f"Rate limit: waiting {wait_time:.2f}s for {domain}")
            await asyncio.sleep(wait_time)

        self.last_request[domain] = datetime.now()

    def set_delay(self, domain, delay):
        """Set crawl-delay for domain (from robots.txt)"""
        self.delays[domain] = delay

# Usage in batch scraper:
rate_limiter = DomainRateLimiter()

async def scrape_url(url):
    domain = urlparse(url).netloc

    # Get and set crawl-delay from robots.txt
    crawl_delay = get_crawl_delay(url)  # From Component 1
    rate_limiter.set_delay(domain, crawl_delay)

    # Wait if needed
    await rate_limiter.wait_if_needed(domain)

    # Now safe to scrape
    result = extract_article(url)
    return result
```

### 🟢 GREEN: Validation

**Test Commands:**
```bash
# Test with multiple URLs from same domain
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.svd.se/article1",
      "https://www.svd.se/article2",
      "https://www.svd.se/article3"
    ]
  }'

# Expected: Should see rate limit delays in logs
# Expected: Requests spaced by crawl-delay (1-5 seconds)

# Check logs for User-Agent
docker logs ydun-scraper | grep "YdunScraperBot"

# Expected: See bot identification in logs

# Monitor disconnections
docker logs ydun-scraper | grep "RemoteDisconnected" | wc -l

# Expected: Significant reduction from 187 baseline
```

**Performance Test:**
```bash
# Send 50 URLs, mixed domains
time curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d @test-urls-50.json

# Measure:
# - Total time (should be longer due to delays - EXPECTED)
# - Success rate (should be higher - disconnections reduced)
# - Compliance logs (all TDM decisions logged)
```

**Validation Criteria:**
- [ ] User-Agent properly identifies bot
- [ ] Concurrency reduced to 3 (or configurable)
- [ ] Per-domain delays enforced
- [ ] Disconnections reduced by 80%+ (target: <40 from 187)
- [ ] Performance acceptable (longer runtime expected, but higher success)
- [ ] Compliance logs show TDM decisions

### 🔵 CHECKPOINT

**Deliverables:**
- Updated User-Agent in all HTTP requests
- Reduced concurrency to 3
- DomainRateLimiter class implemented
- Per-domain crawl-delay enforcement
- Tests passing
- Live validation showing reduced disconnections

**Rollback Procedure:**
```bash
cd ~/ydun-scraper
git revert <commit-hash>
docker compose -f ~/dev-network/beast/docker/docker-compose.yml restart ydun-scraper
# Time to rollback: 2 minutes
```

---

## Component 4: Integration & Testing

### 🔴 RED: Implementation

**File:** Create `tests/test_legal_compliance.py`

**Unit Tests:**
```python
import pytest
from src.tdm_compliance import check_tdm_optout, check_robots_txt
from src.article_extractor import extract_article

class TestRobotsCompliance:
    """Test robots.txt compliance"""

    def test_robots_txt_allowed_url(self):
        """Test URL that should be allowed"""
        url = "https://example.com/article"
        assert check_robots_txt(url) == True

    def test_robots_txt_disallowed_url(self):
        """Test URL that should be blocked"""
        url = "https://www.google.com/search?q=test"
        # Google blocks scrapers in robots.txt
        assert check_robots_txt(url) == False

    def test_crawl_delay_parsing(self):
        """Test crawl-delay extraction from robots.txt"""
        url = "https://www.svd.se/"
        delay = get_crawl_delay(url)
        assert delay >= 1.0  # Should respect minimum delay

class TestTDMCompliance:
    """Test TDM opt-out detection"""

    def test_tdm_optout_meta_tag(self):
        """Test TDM opt-out via meta tag"""
        html = '<html><head><meta name="tdm-reservation" content="1"/></head></html>'
        allowed, reason = check_tdm_optout("https://example.com", html)
        assert allowed == False
        assert "tdm-reservation" in reason

    def test_tdm_allowed_no_signals(self):
        """Test TDM allowed when no opt-out signals"""
        html = '<html><head></head><body>Content</body></html>'
        allowed, reason = check_tdm_optout("https://example.com", html)
        assert allowed == True

class TestRateLimiting:
    """Test per-domain rate limiting"""

    @pytest.mark.asyncio
    async def test_domain_rate_limit(self):
        """Test delays are enforced per domain"""
        from src.batch_scraper import DomainRateLimiter
        import time

        limiter = DomainRateLimiter()
        limiter.set_delay("example.com", 2.0)

        # First request - should proceed immediately
        start = time.time()
        await limiter.wait_if_needed("example.com")
        first_duration = time.time() - start
        assert first_duration < 0.1

        # Second request - should wait ~2 seconds
        start = time.time()
        await limiter.wait_if_needed("example.com")
        second_duration = time.time() - start
        assert 1.8 <= second_duration <= 2.2  # Allow some variance
```

**Create test data file:** `tests/test-urls-compliance.json`
```json
{
  "urls": [
    "https://www.svd.se/nyheter/inrikes/test",
    "https://www.aftonbladet.se/nyheter/test",
    "https://www.expressen.se/nyheter/test"
  ]
}
```

### 🟢 GREEN: Validation

**Test Suite:**
```bash
# Run all unit tests
pytest tests/ -v --cov=src

# Expected coverage:
# - article_extractor.py: 80%+
# - tdm_compliance.py: 90%+
# - batch_scraper.py: 70%+

# Run compliance-specific tests
pytest tests/test_legal_compliance.py -v

# Expected: All tests passing

# Integration test with real URLs
python -m pytest tests/test_integration_compliance.py -v --log-cli-level=INFO

# Expected: See compliance logs, delayed requests, opt-out detections
```

**Live Testing (Low Volume):**
```bash
# Test with 10 Scandinavian news URLs
curl -X POST https://scrape.kitt.agency/scrape \
  -H "Content-Type: application/json" \
  -d @tests/test-urls-compliance.json

# Monitor logs
ssh jimmyb@192.168.68.100
docker logs ydun-scraper --tail 100 -f

# Look for:
# - "TDM ALLOWED" or "TDM BLOCKED" logs
# - "Rate limit: waiting X.Xs for domain.com"
# - "robots.txt disallows scraping"
# - Reduced "RemoteDisconnected" warnings
```

**Success Metrics:**
- [ ] All unit tests passing (pytest)
- [ ] Test coverage >75% for compliance modules
- [ ] Live test shows compliance logs
- [ ] Disconnections reduced significantly
- [ ] No regression in extraction quality

### 🔵 CHECKPOINT

**Deliverables:**
- Complete test suite (`test_legal_compliance.py`)
- All tests passing
- Live validation complete
- Compliance logging working

**Rollback Procedure:**
```bash
git revert <commit-hash>
docker compose restart ydun-scraper
# Time to rollback: 2 minutes
```

---

## Component 5: Docker Rebuild & Deployment

### 🔴 RED: Implementation

**Update Docker image with new dependencies:**

**File:** `requirements.txt` (if not already present)
```txt
# Add if missing:
beautifulsoup4>=4.12.0  # For HTML parsing
lxml>=4.9.0             # BS4 parser backend
```

**Rebuild and deploy:**
```bash
cd ~/ydun-scraper

# Rebuild Docker image
docker build -t ydun-scraper:legal-compliance .

# Stop current container
cd ~/dev-network/beast/docker
docker compose stop ydun-scraper

# Update image tag (if using docker-compose)
# OR deploy new version
docker run -d --name ydun-scraper-compliance \
  -p 5000:5000 \
  --network monitoring \
  ydun-scraper:legal-compliance

# OR update docker-compose.yml and:
docker compose up -d ydun-scraper
```

### 🟢 GREEN: Validation

**Deployment Validation:**
```bash
# Check service is running
docker ps | grep ydun-scraper

# Expected: Status "Up" with "(healthy)" if healthcheck configured

# Test health endpoint
curl http://localhost:5000/health

# Expected: {"status": "healthy"}

# Test scraping endpoint
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.hs.fi/politiikka/test"]}'

# Expected: Article extracted with compliance logs

# Check external access
curl https://scrape.kitt.agency/health

# Expected: 200 OK

# Monitor Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up{job=\"ydun-scraper\"}

# Expected: "value": [timestamp, "1"]
```

**Compliance Validation:**
```bash
# Send 20 mixed-domain URLs
curl -X POST https://scrape.kitt.agency/scrape \
  -H "Content-Type: application/json" \
  -d @tests/test-urls-20-mixed.json > compliance-test-output.json

# Analyze logs
docker logs ydun-scraper --since 5m | grep -E "TDM|robots.txt|Rate limit"

# Count disconnections
docker logs ydun-scraper --since 5m | grep "RemoteDisconnected" | wc -l

# Expected: <5 (vs 187 baseline - 97% reduction)
```

**Validation Criteria:**
- [ ] Service deployed and healthy
- [ ] External HTTPS access working
- [ ] Compliance modules active (logs show TDM decisions)
- [ ] Rate limiting enforced (logs show delays)
- [ ] Disconnections drastically reduced (<10 in test batch)
- [ ] Extraction success rate maintained or improved
- [ ] Prometheus monitoring shows service up

### 🔵 CHECKPOINT

**Deliverables:**
- Service deployed with compliance features
- All validation tests passing
- Live testing shows compliance working
- Disconnections reduced by 90%+
- External access functional

**Rollback Procedure:**
```bash
cd ~/dev-network/beast/docker
docker compose stop ydun-scraper
docker compose up -d ydun-scraper  # Uses previous image
# Time to rollback: 2 minutes
```

---

## Documentation Updates

### 🔴 RED: Update Docs

**Files to update:**

**1. README.md:**
- Add "Legal Compliance" section
- Note robots.txt respect
- Note TDM compliance framework
- Update User-Agent info

**2. DEPLOYMENT.md:**
- Add compliance validation steps
- Update environment variables (if needed)
- Document new dependencies

**3. LIVE_TESTING_RESULTS.md:**
- Add "Week 1 Implementation - COMPLETE" section
- Document before/after metrics (disconnections, success rate)
- Mark observations 2, 4, 5 as resolved

**4. Create COMPLIANCE.md:**
```markdown
# Legal Compliance Framework

## TDM Legal Basis (EU DSM Directive Article 4)

Ydun Scraper operates under Text and Data Mining exception...

## Implemented Controls

1. robots.txt Compliance ✅
2. TDMRep Opt-Out Detection ✅
3. User-Agent Identification ✅
4. Per-Domain Rate Limiting ✅
5. Audit Trail Logging ✅

## Output Restrictions

[Document summary format restrictions per Article 15]

## GDPR Compliance

[Document retention policies, access controls]
```

### 🟢 GREEN: Validation

**Documentation Checklist:**
- [ ] All docs updated with new compliance features
- [ ] Dates current (2025-10-19)
- [ ] Factual language (no marketing claims)
- [ ] Clear instructions for operators
- [ ] Compliance framework documented

### 🔵 CHECKPOINT

**Deliverables:**
- All documentation updated
- COMPLIANCE.md created
- Clear audit trail for legal review

---

## Final Validation & Approval Gate

### Beast Executor Checklist

Before marking complete, verify:

**Code Quality:**
- [ ] All 4 components implemented
- [ ] Unit tests passing (pytest)
- [ ] Code follows project standards (AGENTS.md)
- [ ] No new linting errors

**Compliance:**
- [ ] robots.txt respected (validated with test URLs)
- [ ] TDMRep detection working
- [ ] User-Agent identifies as TDM bot
- [ ] Per-domain rate limiting enforced
- [ ] Audit trail logging functional

**Deployment:**
- [ ] Docker image rebuilt
- [ ] Service deployed and healthy
- [ ] External access working (https://scrape.kitt.agency)
- [ ] Prometheus monitoring shows service up

**Performance:**
- [ ] Remote disconnections reduced 80%+ (target: <40 from 187)
- [ ] CDATA failures remain (deferred to Week 2)
- [ ] Connection pool warnings reduced 50%+ (target: <250 from 507)
- [ ] Extraction success rate maintained (within 5% of baseline)

**Documentation:**
- [ ] README.md updated
- [ ] DEPLOYMENT.md updated
- [ ] COMPLIANCE.md created
- [ ] LIVE_TESTING_RESULTS.md updated with outcomes

### Report to Orchestrator

**When complete, report in GitHub issue or commit message:**

```
Week 1 Legal Compliance - COMPLETE ✅

Implemented:
✅ robots.txt compliance (trafilatura + fallback)
✅ TDMRep opt-out detection (HTTP headers + meta tags)
✅ User-Agent identification (YdunScraperBot/1.0)
✅ Per-domain rate limiting (crawl-delay from robots.txt)
✅ Audit trail logging

Results:
- Remote disconnections: 187 → [X] ([XX]% reduction)
- Success rate: [baseline]% → [new]%
- Compliance: 0/5 controls → 5/5 controls ✅
- Legal status: EXPOSED → COMPLIANT ✅

Validation:
- All unit tests passing
- Live testing complete
- Service operational
- Documentation updated

Next: Week 2 technical fixes (CDATA wrapping, connection pool)
```

---

## Risk Assessment

### Implementation Risks

**Low Risk:**
- robots.txt checking (trafilatura has built-in support)
- User-Agent update (configuration change)
- Unit tests (new code, no regression)

**Medium Risk:**
- Rate limiting (may slow throughput - EXPECTED)
- TDMRep detection (new dependency on BeautifulSoup)
- Concurrency reduction (performance impact)

**Mitigation:**
- Test thoroughly with small batches first
- Monitor performance metrics before/after
- Keep rollback simple (git revert + restart)

### Operational Risks

**Before Implementation:**
- ❌ Legal exposure (violating opt-outs)
- ❌ Site blocking (187 disconnections)
- ❌ IP bans possible

**After Implementation:**
- ✅ Legal compliance (EU DSM Article 4)
- ✅ Ethical bot behavior
- ✅ Reduced site blocking
- ⚠️ Slower throughput (ACCEPTABLE for compliance)

---

## Success Criteria

**MUST HAVE (Week 1):**
- [x] robots.txt compliance implemented
- [x] TDMRep opt-out detection working
- [x] User-Agent identifies as TDM bot
- [x] Per-domain rate limiting enforced
- [x] Disconnections reduced 80%+
- [x] All tests passing
- [x] Service deployed and operational

**NICE TO HAVE (Deferred):**
- [ ] CDATA URL fix (Week 2)
- [ ] Connection pool increase (Week 2)
- [ ] GDPR retention policies (Week 3)
- [ ] Output summary restrictions (Week 3)

---

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Component 1: robots.txt | 1 hour |
| Component 2: TDMRep | 1.5 hours |
| Component 3: Rate limiting | 1.5 hours |
| Component 4: Testing | 1 hour |
| Component 5: Deployment | 30 minutes |
| Documentation | 30 minutes |
| **Total** | **6 hours** |

**Recommended:** Execute over 1-2 sessions with checkpoints between components.

---

## Files to Modify

**Source Code:**
- `src/article_extractor.py` (add robots.txt + TDM checks)
- `src/batch_scraper.py` (User-Agent, rate limiting, concurrency)
- `src/tdm_compliance.py` (NEW - TDM opt-out detection)
- `config.py` or similar (User-Agent constant)

**Tests:**
- `tests/test_legal_compliance.py` (NEW)
- `tests/test-urls-compliance.json` (NEW - test data)

**Documentation:**
- `README.md` (add compliance section)
- `DEPLOYMENT.md` (update deployment steps)
- `LIVE_TESTING_RESULTS.md` (add Week 1 outcomes)
- `COMPLIANCE.md` (NEW - legal framework)

**Docker:**
- `requirements.txt` (add beautifulsoup4, lxml if missing)
- Rebuild image: `docker build -t ydun-scraper:legal-compliance .`

---

## Appendix: Code Examples

### Crawl-Delay Implementation

```python
# In batch_scraper.py
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def get_crawl_delay(url):
    """Get crawl-delay from robots.txt"""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{domain}/robots.txt"

    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
        delay = parser.crawl_delay("YdunScraperBot/1.0")
        logger.info(f"robots.txt crawl-delay for {domain}: {delay}s")
        return delay if delay else 1.0
    except Exception as e:
        logger.warning(f"Could not read robots.txt for {domain}: {e}")
        return 1.0  # Default to 1 second
```

### User-Agent Header

```python
# In batch_scraper.py or config.py
USER_AGENT = 'YdunScraperBot/1.0 (+https://kitt.agency/bot; TDM for news summarization; contact@kitt.agency)'

# In all HTTP requests:
headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9'
}

response = requests.get(url, headers=headers)
```

---

## Orchestrator Approval Gate

**After Beast completes implementation, Orchestrator will:**

1. **Pull changes from GitHub**
   ```bash
   cd ~/ydun-scraper
   git pull
   ```

2. **Review code changes**
   - Check compliance implementation quality
   - Verify tests are comprehensive
   - Review documentation updates

3. **Audit live results**
   - Review disconnection reduction metrics
   - Verify compliance logs
   - Check performance impact

4. **Approve or Request Iteration**
   - ✅ APPROVE: Merge, mark checkpoint complete
   - 🔄 ITERATE: Provide feedback, Beast implements fixes

---

**Execution Spec Status:** 🔴 RED (Ready for Beast execution)
**Created:** 2025-10-19
**Orchestrator:** Chromebook
**Executor:** Beast
**Estimated Duration:** 6 hours
**Priority:** 🔴 CRITICAL

---

**This spec follows Jimmy's Workflow (RED→GREEN→CHECKPOINT) for autonomous execution by Beast.**
