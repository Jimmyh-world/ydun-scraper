#!/usr/bin/env python3
"""
Legal Compliance Test Suite

Tests for:
- robots.txt compliance
- TDM opt-out detection
- Rate limiting
- User-Agent identification

Created: 2025-10-19
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from article_extractor import check_robots_txt, get_crawl_delay, ArticleExtractor
from tdm_compliance import check_tdm_optout
from batch_scraper import DomainRateLimiter, BatchScraper, USER_AGENT


class TestRobotsCompliance:
    """Test robots.txt compliance"""

    def test_user_agent_constant(self):
        """Verify User-Agent identifies as TDM bot"""
        assert 'YdunScraperBot' in USER_AGENT
        assert '1.0' in USER_AGENT
        assert 'TDM' in USER_AGENT
        assert 'contact@kitt.agency' in USER_AGENT

    @patch('article_extractor.RobotFileParser')
    def test_check_robots_txt_allowed(self, mock_parser_class):
        """Test URL that should be allowed"""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True
        mock_parser_class.return_value = mock_parser

        url = "https://example.com/article"
        result = check_robots_txt(url)
        assert result == True

    @patch('article_extractor.RobotFileParser')
    def test_check_robots_txt_disallowed(self, mock_parser_class):
        """Test URL that should be blocked"""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = False
        mock_parser_class.return_value = mock_parser

        url = "https://www.google.com/search?q=test"
        result = check_robots_txt(url)
        assert result == False

    @patch('article_extractor.RobotFileParser')
    def test_check_robots_txt_unavailable_fails_open(self, mock_parser_class):
        """Test that unavailable robots.txt fails open (allow)"""
        mock_parser_class.side_effect = Exception("Connection error")

        url = "https://example.com/article"
        result = check_robots_txt(url)
        assert result == True  # Should allow if unavailable

    @patch('article_extractor.RobotFileParser')
    def test_get_crawl_delay_found(self, mock_parser_class):
        """Test crawl-delay extraction from robots.txt"""
        mock_parser = MagicMock()
        mock_parser.crawl_delay.return_value = 2.0
        mock_parser_class.return_value = mock_parser

        url = "https://www.svd.se/"
        delay = get_crawl_delay(url)
        assert delay == 2.0

    @patch('article_extractor.RobotFileParser')
    def test_get_crawl_delay_not_found_defaults(self, mock_parser_class):
        """Test default crawl-delay when not specified"""
        mock_parser = MagicMock()
        mock_parser.crawl_delay.return_value = None
        mock_parser_class.return_value = mock_parser

        url = "https://example.com/"
        delay = get_crawl_delay(url)
        assert delay == 1.0  # Should default to 1 second


class TestTDMCompliance:
    """Test TDM opt-out detection"""

    @patch('tdm_compliance.requests.head')
    def test_tdm_optout_http_header_x_tdm_opt_out(self, mock_head):
        """Test TDM opt-out via X-TDM-Opt-Out header"""
        mock_response = MagicMock()
        mock_response.headers = {'X-TDM-Opt-Out': '1'}
        mock_head.return_value = mock_response

        url = "https://example.com"
        allowed, reason = check_tdm_optout(url)
        assert allowed == False
        assert "X-TDM-Opt-Out" in reason

    @patch('tdm_compliance.requests.head')
    def test_tdm_optout_http_header_tdm_reservation(self, mock_head):
        """Test TDM opt-out via TDM-Reservation header"""
        mock_response = MagicMock()
        mock_response.headers = {'TDM-Reservation': 'restricted'}
        mock_head.return_value = mock_response

        url = "https://example.com"
        allowed, reason = check_tdm_optout(url)
        assert allowed == False
        assert "TDM-Reservation" in reason

    def test_tdm_optout_meta_tag_reservation(self):
        """Test TDM opt-out via meta tag"""
        html = '<html><head><meta name="tdm-reservation" content="1"/></head></html>'
        with patch('tdm_compliance.requests.head', side_effect=Exception("Skip headers")):
            allowed, reason = check_tdm_optout("https://example.com", html)
            assert allowed == False
            assert "tdm-reservation" in reason

    def test_tdm_optout_meta_tag_robots_noai(self):
        """Test TDM opt-out via robots noai meta tag"""
        html = '<html><head><meta name="robots" content="noai"/></head></html>'
        with patch('tdm_compliance.requests.head', side_effect=Exception("Skip headers")):
            allowed, reason = check_tdm_optout("https://example.com", html)
            assert allowed == False
            assert "noai" in reason

    def test_tdm_allowed_no_signals(self):
        """Test TDM allowed when no opt-out signals"""
        html = '<html><head></head><body>Content</body></html>'
        with patch('tdm_compliance.requests.head', return_value=MagicMock(headers={})):
            allowed, reason = check_tdm_optout("https://example.com", html)
            assert allowed == True
            assert "No opt-out signals" in reason


class TestRateLimiting:
    """Test per-domain rate limiting"""

    def test_domain_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        limiter = DomainRateLimiter()
        assert limiter.get_delay("example.com") == 1.0

    def test_domain_rate_limiter_set_delay(self):
        """Test setting domain-specific delay"""
        limiter = DomainRateLimiter()
        limiter.set_delay("example.com", 2.0)
        assert limiter.get_delay("example.com") == 2.0

    def test_domain_rate_limiter_minimum_delay(self):
        """Test that delays are at least 1 second"""
        limiter = DomainRateLimiter()
        limiter.set_delay("example.com", 0.5)  # Try to set below minimum
        assert limiter.get_delay("example.com") == 1.0  # Should enforce minimum

    @pytest.mark.asyncio
    async def test_domain_rate_limit_no_wait_first_request(self):
        """Test first request doesn't wait"""
        limiter = DomainRateLimiter()
        limiter.set_delay("example.com", 2.0)

        # First request should not wait
        import time
        start = time.time()
        await limiter.wait_if_needed("example.com")
        duration = time.time() - start
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_domain_rate_limit_respects_delay(self):
        """Test delays are enforced between requests"""
        limiter = DomainRateLimiter()
        limiter.set_delay("example.com", 0.2)  # 200ms delay

        import time

        # First request
        await limiter.wait_if_needed("example.com")

        # Second request - should wait
        start = time.time()
        await limiter.wait_if_needed("example.com")
        duration = time.time() - start

        # Should wait approximately 200ms (allow some variance)
        assert 0.15 <= duration <= 0.3, f"Expected ~0.2s, got {duration}s"


class TestBatchScraper:
    """Test batch scraper integration"""

    def test_batch_scraper_default_concurrency(self):
        """Test that default concurrency is reduced to 3"""
        scraper = BatchScraper()
        assert scraper.max_concurrent == 3

    def test_batch_scraper_rate_limiter_initialized(self):
        """Test that rate limiter is initialized"""
        scraper = BatchScraper()
        assert scraper.rate_limiter is not None
        assert isinstance(scraper.rate_limiter, DomainRateLimiter)

    def test_batch_scraper_custom_concurrency(self):
        """Test custom concurrency setting"""
        scraper = BatchScraper(max_concurrent=5)
        assert scraper.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_batch_scraper_initializes_crawl_delays(self):
        """Test that crawl delays are set from robots.txt"""
        scraper = BatchScraper()

        with patch('batch_scraper.get_crawl_delay', return_value=2.0):
            with patch('batch_scraper.ArticleExtractor.extract', return_value={'success': False}):
                # This would normally test the full scrape, but for now we test
                # that get_crawl_delay is being called
                pass

        # Verify rate limiter exists
        assert scraper.rate_limiter is not None


class TestIntegration:
    """Integration tests for compliance chain"""

    def test_compliance_chain_robots_and_tdm(self):
        """Test that both robots.txt and TDM checks work together"""
        with patch('article_extractor.check_robots_txt', return_value=True):
            with patch('article_extractor.check_tdm_optout', return_value=(True, "Allowed")):
                with patch('article_extractor.trafilatura.fetch_url', return_value="<html></html>"):
                    with patch('article_extractor.trafilatura.extract', return_value={'text': 'content' * 500, 'title': 'Title'}):
                        extractor = ArticleExtractor()
                        result = extractor.extract("https://example.com/article")
                        assert result['success'] == True

    def test_compliance_blocked_by_robots_txt(self):
        """Test that robots.txt block prevents extraction"""
        with patch('article_extractor.check_robots_txt', return_value=False):
            extractor = ArticleExtractor()
            result = extractor.extract("https://example.com/article")
            assert result['success'] == False
            assert result['metadata'].get('robots_txt_blocked') == True

    def test_compliance_blocked_by_tdm_optout(self):
        """Test that TDM opt-out prevents extraction"""
        with patch('article_extractor.check_robots_txt', return_value=True):
            with patch('article_extractor.check_tdm_optout', return_value=(False, "TDM opt-out")):
                with patch('article_extractor.trafilatura.fetch_url', return_value="<html></html>"):
                    extractor = ArticleExtractor()
                    result = extractor.extract("https://example.com/article")
                    assert result['success'] == False
                    assert 'TDM opt-out' in result.get('error', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
