#!/usr/bin/env python3
"""
TDM (Text and Data Mining) Compliance Module

Implements W3C TDMRep standard for detecting opt-out signals.
Follows EU DSM Directive Article 4 for TDM operations.

Created: 2025-10-19
Author: Beast Executor
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def check_tdm_optout(url: str, html_content: str = None) -> tuple:
    """
    Check for TDM opt-out signals per W3C TDMRep standard

    Checks in order:
    1. HTTP headers (X-TDM-Opt-Out, TDM-Reservation)
    2. HTML meta tags (tdm-reservation, robots noai)
    3. robots.txt directives

    Args:
        url: URL to check
        html_content: Optional HTML content (if already fetched)

    Returns:
        tuple: (allowed: bool, reason: str)
            - allowed=True if no opt-out signals detected
            - reason describes the opt-out signal if blocked
    """
    try:
        # 1. Check HTTP headers
        try:
            response = requests.head(url, timeout=5)

            if 'X-TDM-Opt-Out' in response.headers:
                reason = "HTTP header: X-TDM-Opt-Out present"
                log_tdm_decision(url, False, reason)
                return False, reason

            if 'TDM-Reservation' in response.headers:
                reason = f"HTTP header: TDM-Reservation = {response.headers['TDM-Reservation']}"
                log_tdm_decision(url, False, reason)
                return False, reason

        except requests.RequestException as e:
            logger.debug(f"Could not check HTTP headers for {url}: {e}")
            # Continue checking other signals

        # 2. Check HTML meta tags (if content provided)
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')

                # Check for TDMRep meta tag
                tdm_meta = soup.find('meta', attrs={'name': 'tdm-reservation'})
                if tdm_meta and tdm_meta.get('content') == '1':
                    reason = "HTML meta: tdm-reservation = 1"
                    log_tdm_decision(url, False, reason)
                    return False, reason

                # Check for AI training opt-out (common pattern)
                ai_meta = soup.find('meta', attrs={'name': 'robots'})
                if ai_meta:
                    content = ai_meta.get('content', '').lower()
                    if 'noai' in content or 'noimageai' in content:
                        reason = f"HTML meta robots: {content}"
                        log_tdm_decision(url, False, reason)
                        return False, reason

            except Exception as e:
                logger.debug(f"Could not parse HTML for {url}: {e}")
                # Continue to allow

        # 3. Check robots.txt for TDM-specific directives
        # (Already handled in article_extractor.py Component 1)

        # No opt-out signals detected
        reason = "No opt-out signals detected"
        log_tdm_decision(url, True, reason)
        return True, reason

    except Exception as e:
        logger.error(f"Error checking TDM opt-out for {url}: {e}")
        # Fail open - allow if error
        log_tdm_decision(url, True, f"Error during check: {e}")
        return True, f"Error during check: {e}"


def log_tdm_decision(url: str, allowed: bool, reason: str) -> None:
    """
    Log TDM compliance decision for audit trail

    Args:
        url: URL being evaluated
        allowed: Whether scraping is allowed
        reason: Explanation of the decision
    """
    if allowed:
        logger.info(f"TDM ALLOWED: {url} - {reason}")
    else:
        logger.warning(f"TDM BLOCKED: {url} - {reason}")

    # TODO: Consider writing to compliance log file or database for audit trail
    # This would support GDPR compliance requirements
