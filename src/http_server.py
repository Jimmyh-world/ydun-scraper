#!/usr/bin/env python3
"""
HTTP Server for Article Scraper

Provides REST API endpoint for batch scraping.
Designed to be called by Supabase Edge Functions.

Endpoint: POST /scrape
Body: {"urls": ["url1", "url2"], "config": {...}}

Created: 2025-10-09
"""

from flask import Flask, request, jsonify
from batch_scraper import BatchScraper
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ydun-article-scraper"})

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Scrape multiple URLs
    
    Request body:
    {
        "urls": ["url1", "url2", ...],
        "config": {
            "max_concurrent": 10,
            "timeout_per_url": 10
        }
    }
    """
    try:
        data = request.json
        
        if not data or 'urls' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'urls' in request body"
            }), 400
        
        urls = data['urls']
        config = data.get('config', {})
        
        if not urls:
            return jsonify({
                "success": False,
                "error": "Empty URL list"
            }), 400
        
        logger.info(f"🌐 Received scraping request: {len(urls)} URLs")
        
        # Create scraper and run
        max_concurrent = config.get('max_concurrent', 10)
        timeout = config.get('timeout_per_url', 10)
        
        scraper = BatchScraper(max_concurrent=max_concurrent, timeout=timeout)
        result = asyncio.run(scraper.scrape_batch(urls))
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Article Scraper HTTP Server")
    logger.info("   Listening on port 8080")
    logger.info("   Endpoint: POST /scrape")
    app.run(host='0.0.0.0', port=8080, debug=False)
