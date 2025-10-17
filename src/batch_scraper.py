#!/usr/bin/env python3
"""
Batch Article Scraper

Processes multiple URLs concurrently and outputs results as JSON.

Usage:
    echo '{"urls": ["url1", "url2"]}' | python batch_scraper.py
    python batch_scraper.py --urls url1 url2 url3

Created: 2025-10-09
Following: Jimmy's Workflow, AGENTS.md principles
"""

import asyncio
import aiohttp
import sys
import json
import time
from typing import List, Dict, Any
from article_extractor import ArticleExtractor
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class BatchScraper:
    """
    Batch article scraper with concurrent processing
    """

    def __init__(self, max_concurrent: int = 10, timeout: int = 10):
        """
        Args:
            max_concurrent: Maximum concurrent URL fetches (default: 10)
            timeout: Timeout per URL in seconds (default: 10)
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.extractor = ArticleExtractor(timeout=timeout)

    async def scrape_batch(self, urls: List[str]) -> Dict[str, Any]:
        """
        Scrape multiple URLs concurrently

        Args:
            urls: List of article URLs to scrape

        Returns:
            Dict with results and statistics
        """
        start_time = time.time()

        logger.info(f"🤖 Batch Scraper Starting")
        logger.info(f"   URLs: {len(urls)}")
        logger.info(f"   Concurrency: {self.max_concurrent}")
        logger.info(f"   Timeout: {self.timeout}s per URL")
        logger.info("")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process URLs concurrently
        tasks = [self._scrape_with_limit(url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Calculate statistics
        succeeded = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        avg_length = 0
        if succeeded:
            total_length = sum(r['metadata'].get('content_length', 0) for r in succeeded)
            avg_length = total_length / len(succeeded)

        stats = {
            'total': len(urls),
            'succeeded': len(succeeded),
            'failed': len(failed),
            'success_rate': len(succeeded) / len(urls) if urls else 0,
            'avg_content_length': int(avg_length),
            'duration_seconds': round(duration, 2),
            'urls_per_second': round(len(urls) / duration, 2) if duration > 0 else 0
        }

        logger.info("")
        logger.info(f"📊 Batch Complete:")
        logger.info(f"   Total: {stats['total']}")
        logger.info(f"   Succeeded: {stats['succeeded']}")
        logger.info(f"   Failed: {stats['failed']}")
        logger.info(f"   Success Rate: {stats['success_rate']*100:.1f}%")
        logger.info(f"   Avg Content: {stats['avg_content_length']} chars")
        logger.info(f"   Duration: {stats['duration_seconds']}s")
        logger.info("")

        return {
            'success': True,
            'results': results,
            'stats': stats
        }

    async def _scrape_with_limit(self, url: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """
        Scrape single URL with semaphore for concurrency control
        """
        async with semaphore:
            # Run sync extractor in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.extractor.extract, url)


async def main():
    """Main entry point"""

    # Parse input (JSON from stdin or command line args)
    if len(sys.argv) > 1 and sys.argv[1] == '--urls':
        urls = sys.argv[2:]
        config = {}
    else:
        # Read JSON from stdin
        try:
            input_data = json.load(sys.stdin)
            urls = input_data.get('urls', [])
            config = input_data.get('config', {})
        except:
            logger.error("❌ Invalid JSON input")
            logger.error("Usage: echo '{\"urls\": [\"url1\", \"url2\"]}' | python batch_scraper.py")
            sys.exit(1)

    if not urls:
        logger.error("❌ No URLs provided")
        sys.exit(1)

    # Create scraper
    max_concurrent = config.get('max_concurrent', 10)
    timeout = config.get('timeout_per_url', 10)

    scraper = BatchScraper(max_concurrent=max_concurrent, timeout=timeout)

    # Scrape
    result = await scraper.scrape_batch(urls)

    # Output JSON to stdout
    print(json.dumps(result, indent=2))

    # Exit code based on success rate
    if result['stats']['success_rate'] < 0.5:
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
