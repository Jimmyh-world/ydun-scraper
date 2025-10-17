#!/usr/bin/env python3
"""
Continuous Scraping Poller

Polls database for articles with needs_scraping=true, scrapes them, updates content.
Runs continuously - safe for overnight operation.

Created: 2025-10-09
Following: Jimmy's Workflow, AGENTS.md principles (KISS, security)
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import List, Dict, Any
from article_extractor import ArticleExtractor
from batch_scraper import BatchScraper

# Database connection with proper pooling
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingPoller:
    """Continuously polls for articles needing scraping with robust connection management"""

    def __init__(self, db_url: str, poll_interval: int = 30, batch_size: int = 20):
        self.db_url = db_url
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.scraper = BatchScraper(max_concurrent=10, timeout=10)

        # Create connection pool (min=1, max=5 connections)
        # Pool automatically handles connection lifecycle
        self.connection_pool = pool.SimpleConnectionPool(1, 5, self.db_url)
        logger.info("✅ Database connection pool created (1-5 connections)")

    def get_connection(self):
        """Get connection from pool with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = self.connection_pool.getconn()
                # Test connection is alive
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return conn
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise

    def return_connection(self, conn):
        """Return connection to pool"""
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning connection: {str(e)}")

    def reload_config(self):
        """Reload configuration from database (for dynamic mode switching)"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute("SELECT poll_interval, batch_size FROM scraper_config LIMIT 1")
            config = cur.fetchone()

            if config:
                # Update instance variables if changed
                if config['poll_interval'] != self.poll_interval:
                    logger.info(f"🔄 Poll interval changed: {self.poll_interval}s → {config['poll_interval']}s")
                    self.poll_interval = config['poll_interval']

                if config['batch_size'] != self.batch_size:
                    logger.info(f"🔄 Batch size changed: {self.batch_size} → {config['batch_size']}")
                    self.batch_size = config['batch_size']

            conn.commit()

        except Exception as e:
            logger.warning(f"Could not reload config: {str(e)}")
        finally:
            cur.close()
            self.return_connection(conn)

    def get_articles_needing_scraping(self) -> List[Dict[str, Any]]:
        """Query database for articles needing scraping"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute("""
                SELECT id, url, title, country, source_name
                FROM articles
                WHERE content IS NULL
                  AND url IS NOT NULL
                  AND metadata->>'needs_scraping' = 'true'
                ORDER BY fetched_at DESC
                LIMIT %s
            """, (self.batch_size,))

            articles = cur.fetchall()
            conn.commit()  # Commit even SELECTs (best practice for long-running)
            return [dict(a) for a in articles]

        finally:
            cur.close()
            self.return_connection(conn)

    def update_article_content(self, article_id: str, content: str, metadata: dict):
        """Update article with scraped content"""
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Update content and remove needs_scraping flag
            cur.execute("""
                UPDATE articles
                SET content = %s,
                    metadata = metadata || %s::jsonb
                WHERE id = %s
            """, (content, json.dumps(metadata), article_id))

            conn.commit()

        finally:
            cur.close()
            self.return_connection(conn)
    
    async def process_batch(self, articles: List[Dict[str, Any]]):
        """Scrape batch of articles and update database"""
        if not articles:
            return
        
        logger.info(f"📰 Processing batch of {len(articles)} articles")
        
        # Extract URLs
        urls = [a['url'] for a in articles]
        
        # Scrape
        result = await self.scraper.scrape_batch(urls)
        
        # Update database
        successful = 0
        failed = 0
        
        for i, article in enumerate(articles):
            scrape_result = result['results'][i]
            
            if scrape_result['success']:
                content = scrape_result['content']
                metadata = {
                    'needs_scraping': False,
                    'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'scraper_version': 'v1.0',
                    'content_length': scrape_result['metadata']['content_length']
                }
                
                self.update_article_content(article['id'], content, metadata)
                successful += 1
            else:
                # Mark as failed (stop retrying)
                metadata = {
                    'needs_scraping': False,
                    'scraping_failed': True,
                    'scraping_error': scrape_result['error']
                }
                self.update_article_content(article['id'], '', metadata)
                failed += 1
        
        logger.info(f"✅ Batch complete: {successful} scraped, {failed} failed")
    
    async def run(self):
        """Main polling loop"""
        logger.info("🚀 Starting Continuous Scraping Poller")
        logger.info(f"   Database: {self.db_url[:50]}...")
        logger.info(f"   Poll interval: {self.poll_interval}s")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info("")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1

                # Reload config from database (every 10 polls = ~5 minutes)
                if iteration % 10 == 1:
                    self.reload_config()

                logger.info(f"🔄 Poll #{iteration}")

                # Get articles needing scraping
                articles = self.get_articles_needing_scraping()
                
                if articles:
                    logger.info(f"   Found {len(articles)} articles to scrape")
                    await self.process_batch(articles)
                else:
                    logger.info(f"   No articles need scraping (sleeping {self.poll_interval}s)")
                
                # Sleep before next poll
                await asyncio.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping poller (Ctrl+C)")
                break
            except Exception as e:
                logger.error(f"❌ Error in polling loop: {str(e)}")
                logger.info(f"   Retrying in {self.poll_interval}s...")
                await asyncio.sleep(self.poll_interval)

if __name__ == '__main__':
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("❌ DATABASE_URL environment variable not set!")
        logger.error("   Set it in docker run command:")
        logger.error("   docker run -e DATABASE_URL='postgresql://...' ...")
        sys.exit(1)
    
    # Create and run poller
    poller = ScrapingPoller(
        db_url=db_url,
        poll_interval=30,  # Check every 30 seconds
        batch_size=20      # Process 20 articles per batch
    )
    
    asyncio.run(poller.run())
