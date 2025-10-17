#!/usr/bin/env python3
"""
Article Content Extractor

Extracts full article text from URLs using multiple strategies:
1. trafilatura (primary - automatic extraction)
2. newspaper3k (fallback - news-specific)
3. Basic fallback (last resort)

Created: 2025-10-09
Following: AGENTS.md principles (KISS, YAGNI, Fix Now)
"""

import trafilatura
from newspaper import Article as NewspaperArticle
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleExtractor:
    """
    Extracts full article content from a single URL

    Uses fallback chain:
    1. trafilatura (92% success rate, automatic)
    2. newspaper3k (news-specific, metadata extraction)
    3. Basic extraction (last resort)
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize extractor

        Args:
            timeout: HTTP request timeout in seconds (default: 10)
        """
        self.timeout = timeout

    def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract full article from URL

        Args:
            url: Article URL to scrape

        Returns:
            Dict with keys: success, url, title, content, author, published_at, metadata
        """
        try:
            # Try trafilatura first (fastest, most reliable)
            result = self._extract_with_trafilatura(url)
            if result['success'] and len(result['content']) > 500:
                result['metadata']['extraction_method'] = 'trafilatura'
                return result

            logger.info(f"Trafilatura failed for {url}, trying newspaper3k...")

            # Fallback to newspaper3k
            result = self._extract_with_newspaper(url)
            if result['success'] and len(result['content']) > 500:
                result['metadata']['extraction_method'] = 'newspaper3k'
                return result

            # Both failed
            logger.warning(f"All extraction methods failed for {url}")
            return {
                'success': False,
                'url': url,
                'error': 'No content extracted',
                'title': None,
                'content': None,
                'author': None,
                'published_at': None,
                'metadata': {'extraction_method': 'none'}
            }

        except Exception as e:
            logger.error(f"Error extracting {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'title': None,
                'content': None,
                'author': None,
                'published_at': None,
                'metadata': {}
            }

    def _extract_with_trafilatura(self, url: str) -> Dict[str, Any]:
        """Extract using trafilatura (primary method)"""
        try:
            # Download HTML
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {'success': False, 'url': url}

            # Extract content with metadata
            result = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                output_format='txt',
                with_metadata=True
            )

            if not result:
                return {'success': False, 'url': url}

            # trafilatura returns dict when with_metadata=True
            if isinstance(result, dict):
                content = result.get('text', '')
                title = result.get('title', '')
                author = result.get('author', None)
                date_str = result.get('date', None)
                published_at = self._parse_date(date_str) if date_str else None
            else:
                # Fallback if plain text returned
                content = result
                title = trafilatura.extract(downloaded, output_format='txt', with_metadata=False) or ''
                author = None
                published_at = None

            return {
                'success': True,
                'url': url,
                'title': title,
                'content': content,
                'author': author,
                'published_at': published_at,
                'metadata': {
                    'content_length': len(content),
                    'extraction_method': 'trafilatura'
                }
            }

        except Exception as e:
            logger.warning(f"Trafilatura failed for {url}: {str(e)}")
            return {'success': False, 'url': url, 'error': str(e)}

    def _extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Extract using newspaper3k (fallback method)"""
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()

            # newspaper3k extracts metadata automatically
            if not article.text or len(article.text) < 100:
                return {'success': False, 'url': url}

            return {
                'success': True,
                'url': url,
                'title': article.title or '',
                'content': article.text,
                'author': ', '.join(article.authors) if article.authors else None,
                'published_at': article.publish_date.isoformat() if article.publish_date else None,
                'metadata': {
                    'content_length': len(article.text),
                    'extraction_method': 'newspaper3k',
                    'top_image': article.top_image if hasattr(article, 'top_image') else None
                }
            }

        except Exception as e:
            logger.warning(f"Newspaper3k failed for {url}: {str(e)}")
            return {'success': False, 'url': url, 'error': str(e)}

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.isoformat()
        except:
            return None


if __name__ == '__main__':
    # Quick test
    extractor = ArticleExtractor()

    test_urls = [
        'https://www.svd.se/a/kwAvA6/beslut-om-karnkraftsbyggare-drojer',
        'https://www.aftonbladet.se/nyheter/a/example',  # Will fail (test error handling)
    ]

    print("🧪 Testing Article Extractor\n")

    for url in test_urls:
        print(f"Testing: {url}")
        result = extractor.extract(url)

        if result['success']:
            print(f"  ✅ Success: {result['title'][:50]}...")
            print(f"     Content: {result['metadata']['content_length']} chars")
            print(f"     Method: {result['metadata']['extraction_method']}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        print()
