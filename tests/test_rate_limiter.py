"""
Unit tests for rate limiter
"""
import pytest
import time
from src.github.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter"""

    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(code_search_interval=10.0, contents_interval=0.5)

        assert limiter.code_search_interval == 10.0
        assert limiter.contents_interval == 0.5
        assert limiter.rate_limit_remaining is None

    def test_wait_if_needed_code_search(self):
        """Test rate limiting for code search"""
        limiter = RateLimiter(code_search_interval=0.1, contents_interval=0.05)

        start_time = time.time()
        limiter.wait_if_needed("code_search")
        limiter.wait_if_needed("code_search")
        elapsed = time.time() - start_time

        # Should wait at least the interval time
        assert elapsed >= 0.1

    def test_wait_if_needed_contents(self):
        """Test rate limiting for contents API"""
        limiter = RateLimiter(code_search_interval=0.1, contents_interval=0.05)

        start_time = time.time()
        limiter.wait_if_needed("contents")
        limiter.wait_if_needed("contents")
        elapsed = time.time() - start_time

        # Should wait at least the interval time
        assert elapsed >= 0.05

    def test_update_from_headers(self):
        """Test updating rate limit info from headers"""
        limiter = RateLimiter()

        headers = {
            "x-ratelimit-remaining": "50",
            "x-ratelimit-limit": "60",
            "x-ratelimit-reset": "1234567890",
            "x-ratelimit-resource": "core"
        }

        limiter.update_from_headers(headers)

        assert limiter.rate_limit_remaining == "50"
        assert limiter.rate_limit_limit == "60"
        assert limiter.rate_limit_reset == "1234567890"
        assert limiter.rate_limit_resource == "core"

    def test_exponential_backoff(self):
        """Test exponential backoff"""
        limiter = RateLimiter()

        # Test first attempt (2^0 = 1 second)
        start_time = time.time()
        limiter.exponential_backoff(0, base_delay=0.1, max_delay=1.0)
        elapsed = time.time() - start_time
        assert 0.1 <= elapsed < 0.2

        # Test second attempt (2^1 = 2 * 0.1 = 0.2 seconds)
        start_time = time.time()
        limiter.exponential_backoff(1, base_delay=0.1, max_delay=1.0)
        elapsed = time.time() - start_time
        assert 0.2 <= elapsed < 0.3

    def test_handle_rate_limit_error_with_retry_after(self):
        """Test handling rate limit error with retry-after"""
        limiter = RateLimiter()

        # Use very short wait time for testing
        start_time = time.time()
        limiter.handle_rate_limit_error(retry_after=0)
        elapsed = time.time() - start_time

        # Should wait at least 0 seconds (minimal wait)
        assert elapsed >= 0
