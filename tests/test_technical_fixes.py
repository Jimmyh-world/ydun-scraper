#!/usr/bin/env python3
"""
Technical Fixes Test Suite

Tests for:
- URL sanitization (CDATA stripping)
- Connection pooling
- Session management

Created: 2025-10-19
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from article_extractor import sanitize_url, create_session_with_pool


class TestURLSanitization:
    """Test URL sanitization removes CDATA wrapping"""

    def test_sanitize_cdata_wrapped_url(self):
        """Test CDATA tags are removed"""
        dirty = '<![CDATA[https://example.com/article]]>'
        clean = sanitize_url(dirty)
        assert clean == 'https://example.com/article'

    def test_sanitize_clean_url_unchanged(self):
        """Test clean URLs pass through unchanged"""
        url = 'https://example.com/article'
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_whitespace_stripped(self):
        """Test whitespace is stripped"""
        dirty = '  https://example.com/article  '
        clean = sanitize_url(dirty)
        assert clean == 'https://example.com/article'

    def test_sanitize_nested_cdata(self):
        """Test nested or multiple CDATA tags"""
        dirty = '<![CDATA[<![CDATA[https://example.com]]>]]>'
        clean = sanitize_url(dirty)
        assert 'CDATA' not in clean
        assert 'https://' in clean

    def test_sanitize_empty_string(self):
        """Test empty string handling"""
        result = sanitize_url('')
        assert result == ''

    def test_sanitize_none_handling(self):
        """Test None handling"""
        result = sanitize_url(None)
        assert result is None

    def test_sanitize_polish_url_with_cdata(self):
        """Test real-world Polish URL from logs"""
        dirty = '<![CDATA[https://www.rp.pl/spadki-i-darowizny/test]]>'
        clean = sanitize_url(dirty)
        assert clean == 'https://www.rp.pl/spadki-i-darowizny/test'
        assert 'CDATA' not in clean

    def test_sanitize_swedish_url_with_cdata(self):
        """Test Swedish URL with CDATA"""
        dirty = '<![CDATA[https://www.svd.se/a/12345/article-title]]>'
        clean = sanitize_url(dirty)
        assert clean == 'https://www.svd.se/a/12345/article-title'


class TestConnectionPooling:
    """Test connection pool configuration"""

    def test_session_created_with_pool(self):
        """Test session is created with connection pool"""
        session = create_session_with_pool(pool_size=20)
        assert session is not None

        # Check adapter is configured
        adapter = session.get_adapter('https://example.com')
        assert adapter is not None

        # Check pool size
        assert adapter._pool_connections == 10
        assert adapter._pool_maxsize == 20

    def test_session_has_user_agent(self):
        """Test session has proper User-Agent"""
        session = create_session_with_pool()
        user_agent = session.headers.get('User-Agent', '')
        assert 'YdunScraperBot' in user_agent
        assert 'TDM' in user_agent

    def test_session_retry_configured(self):
        """Test retry strategy is configured"""
        session = create_session_with_pool()
        adapter = session.get_adapter('https://example.com')
        assert adapter.max_retries is not None

    def test_session_http_and_https_mounted(self):
        """Test both HTTP and HTTPS adapters are mounted"""
        session = create_session_with_pool()
        http_adapter = session.get_adapter('http://example.com')
        https_adapter = session.get_adapter('https://example.com')
        assert http_adapter is not None
        assert https_adapter is not None

    def test_session_custom_pool_size(self):
        """Test custom pool size configuration"""
        session = create_session_with_pool(pool_size=50)
        adapter = session.get_adapter('https://example.com')
        assert adapter._pool_maxsize == 50

    def test_session_handles_retry_status_codes(self):
        """Test retry strategy includes correct status codes"""
        session = create_session_with_pool()
        adapter = session.get_adapter('https://example.com')
        retry = adapter.max_retries
        # Check that common error codes are in the forcelist
        assert 500 in retry.status_forcelist
        assert 502 in retry.status_forcelist
        assert 503 in retry.status_forcelist
        assert 504 in retry.status_forcelist


class TestIntegration:
    """Integration tests for both fixes"""

    def test_sanitize_and_validate_url_format(self):
        """Test that sanitized URL is valid format"""
        cdata_url = '<![CDATA[https://example.com/test]]>'
        clean = sanitize_url(cdata_url)

        # Should start with https://
        assert clean.startswith('https://')
        # Should not contain CDATA
        assert 'CDATA' not in clean
        # Should not contain angle brackets
        assert '<' not in clean
        assert '>' not in clean

    def test_session_available_for_requests(self):
        """Test that session is available and functional"""
        session = create_session_with_pool()

        # Verify session has required methods
        assert hasattr(session, 'get')
        assert hasattr(session, 'post')
        assert hasattr(session, 'mount')

        # Verify User-Agent is set
        assert session.headers.get('User-Agent') is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
