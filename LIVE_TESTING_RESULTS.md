# Live Testing Results

## Executive Summary: Priority Action Items

| Priority | Issue | Impact | Fix Effort |
|----------|-------|--------|-----------|
| 🔴 CRITICAL | TDM Legal Compliance | Legal liability + IP blocking | High |
| 🔴 CRITICAL | No robots.txt compliance | 187 disconnections, site blocking | Medium |
| 🔴 CRITICAL | CDATA URL wrapping | 30% batch failures | Low |
| 🟠 HIGH | Connection pool exhaustion | 507 warnings, degraded throughput | Low |
| 🟠 HIGH | Remote disconnections | Cascading failures | Medium |

### Implementation Roadmap

**Week 1 (Legal Compliance):**
1. Implement robots.txt parsing + crawl-delay
2. Add TDMRep detection
3. Update User-Agent to identify as TDM bot
4. Reduce concurrency to 1-2 per domain

**Week 2 (Technical Fixes):**
1. Fix CDATA URL wrapping in edge function
2. Increase connection pool size to 20
3. Implement per-domain request throttling

**Week 3 (GDPR/Output Controls):**
1. Implement retention policies
2. Restrict data storage access
3. Build summary output with minimal quotes + links

---

# Live Testing Results

## Observation 1: CDATA-Wrapped URLs Causing Parse Failures

**Date:** 2025-10-18
**Impact:** 30% failure rate in affected batch
**Severity:** Medium

### Issue
URLs from the edge function are being wrapped in XML CDATA tags: `<![CDATA[URL]]>`

**Affected Batch:** 09:35:02 UTC (10 URLs, 70% success rate)

**Failed URLs (3/10):**
- `https://www.rp.pl/spadki-i-darowizny/...`
- `https://www.rp.pl/transport/...`
- `https://cyfrowa.rp.pl/technologie/...`

### Root Cause
When extraction tools attempt to parse CDATA-wrapped URLs, they interpret the tags as part of the URL string, breaking the format:

```
No connection adapters were found for ':/<![CDATA[https:/www.rp.pl/...]]>'
```

Trafilatura and newspaper3k both fail to extract content from malformed URLs.

### Recommended Fix
**Primary:** Fix in edge function (data source responsibility)
- Strip CDATA tags before sending URLs to scraper
- Ensures clean input for all downstream consumers

**Secondary:** Add URL sanitization in `article_extractor.py`
- Defense-in-depth approach
- Gracefully handle any CDATA that slips through

### Status
🔍 Investigation complete - awaiting edge function code review

---

## Observation 2: Connection Pool Exhaustion

**Date:** 2025-10-18
**Impact:** High request volume degradation
**Severity:** High

### Issue
HTTP connection pool is consistently exhausted, causing connections to be discarded.

**Metrics:**
- Total warnings: 507 from urllib3.connectionpool
- Pool size: 1 (per-domain)
- Affected domains (top 10):
  - www.is.fi (38 times)
  - www.sydsvenskan.se (33)
  - www.svd.se (24)
  - www.di.se (22)
  - www.nrk.no (19)
  - www.hs.fi (19)
  - wiadomosci.wp.pl (18)
  - www.aftonbladet.se (16)
  - www.aftenposten.no (16)
  - www.dn.se (15)

**Log Sample:**
```
WARNING:urllib3.connectionpool:Connection pool is full, discarding connection: www.is.fi. Connection pool size: 1
```

### Root Cause
Per-domain connection pool size is set to 1, but concurrency is 10 URLs per batch. When multiple URLs from the same domain are scraped simultaneously, connections get exhausted and discarded.

### Recommended Fix
**Primary:** Increase connection pool size in `batch_scraper.py`
- Use `urllib3.PoolManager` with larger `maxsize` and `block` parameters
- Recommended: `maxsize=20, block=False`

**Secondary:** Implement connection pooling with requests.Session()
- More Pythonic approach
- Better connection reuse

---

## Observation 3: Remote Server Disconnections

**Date:** 2025-10-18
**Impact:** Failed retries consuming resources
**Severity:** Medium

### Issue
Remote servers are closing connections without response, triggering retry logic.

**Metrics:**
- Total remote disconnections: 187
- Affects Scandinavian news sites primarily

**Log Sample:**
```
WARNING:urllib3.connectionpool:Retrying (Retry(total=1, connect=0, read=None, redirect=2, status=None))
after connection broken by 'RemoteDisconnected('Remote end closed connection without response')':
/live/kursraketens-vd-miljonsaljer-aktier-1/
```

### Root Cause
News sites may be:
- Blocking aggressive scraping (connection pooling exhaustion looks like DDoS)
- Have connection limits per IP
- Closing idle connections

### Recommended Fix
**Primary:** Reduce concurrency or add delays between requests
- Lower concurrency from 10 to 5 URLs at a time
- Add 100-200ms delay between requests per domain

**Secondary:** Implement exponential backoff
- Start with 1 retry, increase wait time
- Respect rate-limiting headers

**Tertiary:** Add User-Agent rotation
- Some sites reject requests without proper User-Agent
- Rotate between common browser agents

---

## Observation 4: No robots.txt Compliance

**Date:** 2025-10-18
**Impact:** Legal/ethical & technical stability
**Severity:** Critical

### Issue
The scraper does NOT respect robots.txt files from target websites.

**Current Code Analysis:**
- `batch_scraper.py` (line 16): Uses `aiohttp` with no robots.txt checking
- `article_extractor.py` (line 99): Uses `trafilatura.fetch_url()` without `respect_robots_txt=True`
- `article_extractor.py` (line 150): Uses `newspaper3k` which lacks robots.txt support

**Sample robots.txt violations:**
News sites like www.svd.se, www.aftonbladet.se, www.expressen.se likely specify:
- Crawl delays (e.g., 1-5 seconds between requests)
- Disallowed paths (articles behind paywalls)
- User-Agent specific restrictions

Current 10 concurrent requests completely ignore these rules.

### Root Cause
Extraction libraries were chosen for extraction capability, not web scraping ethics. No intentional robots.txt checking implemented.

### Recommended Fix
**Primary:** Enable robots.txt checking in trafilatura
```python
downloaded = trafilatura.fetch_url(url, respect_robots_txt=True)
```

**Secondary:** Add urllib's RobotFileParser
```python
from urllib.robotparser import RobotFileParser
parser = RobotFileParser()
parser.set_url(f"{domain}/robots.txt")
if parser.can_fetch("*", url):
    # safe to scrape
```

**Tertiary:** Implement crawl-delay respect
- Parse robots.txt `Crawl-delay` directive
- Add delays between requests to same domain
- Cluster URLs by domain, add 1-2 second delays between domain batches

**Critical:** Add proper User-Agent header
- Identify scraper in User-Agent string
- Allow site admins to detect and potentially block if needed
- Currently likely masquerading as regular client

### Status
⚠️ High priority fix - affects legal compliance and may trigger IP blocking

---

## Observation 5: TDM Legal Compliance Framework (Sweden/EU)

**Date:** 2025-10-18
**Impact:** Legal liability & operational legitimacy
**Severity:** Critical (requires proper implementation)

### Legal Status: PERMITTED with Conditions

Under EU DSM Directive (Article 4) and Swedish copyright law, TDM operations for summarization and analysis ARE legally permitted for lawfully accessible content.

**Key Enabler:** Article 4 DSM Directive permits creating and retaining copies for TDM purposes indefinitely.

### Required Compliance Controls

The scraper must implement machine-readable opt-out detection before processing:

#### 1. Opt-Out Detection (REQUIRED)
Must check in order:
- **robots.txt**: `User-agent: *` crawl permissions + crawl-delay
- **TDMRep (W3C)**: Machine-readable opt-out signals (metadata tags)
- **HTTP Headers**: `X-TDM-Opt-Out` or similar policies
- **Terms of Service**: Publisher-specific restrictions

**Current Status:** ❌ NO opt-out detection implemented

#### 2. Output Restrictions (REQUIRED)
Public-facing summaries must follow Article 15 (Press Publishers' Rights):
- Original language summaries (not just raw text)
- **Very short extracts only** - minimal direct quotation
- Always include links back to original sources
- Automatic deduplication to prevent verbatim reproduction

**Current Status:** ❌ NOT APPLICABLE - no summary output yet, but must be designed in

#### 3. Data Storage Architecture (REQUIRED)
- **TDM Store:** Full-text accessible ONLY to processing systems
- **Restricted Access:** No end-user direct access to original articles
- **Retention Policy:** Keep only as long as "necessary for TDM purpose"
- **Metadata:** URLs, titles, timestamps, source attribution

**Current Status:** ⚠️ Unknown - need to audit Supabase storage

#### 4. Rate Limiting & Respect (REQUIRED)
From robots.txt/TDMRep compliance:
- **Crawl-delay:** Parse and respect per-domain delays (typically 1-5 seconds)
- **Request throttling:** Cluster by domain, add delays between batches
- **Concurrent limits:** Reduce from 10 concurrent to 1-2 per domain
- **User-Agent:** Must identify as TDM operation, not masquerade as browser

**Current Status:** ❌ 10 concurrent requests, no delays, no bot identification

#### 5. GDPR Compliance (REQUIRED)
- Legitimate Interest Assessment: TDM for public summary/analysis purposes
- Data minimization: Store only fields necessary for TDM
- Security: Encrypt full-text storage, restrict access
- Retention: Delete after TDM complete or policy period
- Transparency: Disclose in privacy policy that content is being TDM'd

**Current Status:** ⚠️ Unknown - need privacy policy audit

### Implementation Priority

**Phase 1 (CRITICAL):**
1. Add robots.txt parsing + crawl-delay respect
2. Add TDMRep detection support
3. Implement per-domain rate limiting (max 1-2 req/sec per domain)
4. Update User-Agent to identify as TDM bot

**Phase 2 (HIGH):**
5. Implement opt-out logging (compliance audit trail)
6. Add GDPR retention policies
7. Restrict TDM storage access controls

**Phase 3 (MEDIUM):**
8. Implement output summary deduplication
9. Create privacy policy addendum
10. Document Legitimate Interest Assessment

### Risk Analysis

**Without Opt-Out Detection:**
- High legal risk: Violating Article 4 DSM exception by ignoring opt-outs
- High technical risk: Sites aggressively block (explains current 187 disconnections)
- High IP-blocking risk: Detected as non-compliant scraper

**With Full Compliance:**
- Low legal risk: Legitimate TDM operation under DSM Directive
- Reduced technical issues: Sites recognize ethical bot behavior
- Better success rate: Proper delays + rate limiting = fewer blocked requests

### Status
⚠️ CRITICAL - Must implement before scaling. Current implementation is legally exposed.
