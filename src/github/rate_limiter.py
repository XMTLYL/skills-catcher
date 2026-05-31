"""
Rate limiter for GitHub API requests
"""
import time
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter for GitHub API requests

    Monitors x-ratelimit-* headers and enforces rate limits
    """

    def __init__(self, code_search_interval: float = 10.0, contents_interval: float = 0.5):
        """
        Initialize rate limiter

        Args:
            code_search_interval: Seconds between Code Search requests
            contents_interval: Seconds between Contents API requests
        """
        self.code_search_interval = code_search_interval
        self.contents_interval = contents_interval

        self.last_code_search_time = 0
        self.last_contents_time = 0

        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.rate_limit_limit = None
        self.rate_limit_resource = None

    def wait_if_needed(self, resource_type: str = "contents"):
        """
        Wait if necessary to respect rate limits

        Args:
            resource_type: Type of resource ("code_search" or "contents")
        """
        current_time = time.time()

        if resource_type == "code_search":
            elapsed = current_time - self.last_code_search_time
            if elapsed < self.code_search_interval:
                wait_time = self.code_search_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for Code Search")
                time.sleep(wait_time)
            self.last_code_search_time = time.time()

        else:  # contents or other APIs
            elapsed = current_time - self.last_contents_time
            if elapsed < self.contents_interval:
                wait_time = self.contents_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for Contents API")
                time.sleep(wait_time)
            self.last_contents_time = time.time()

    def update_from_headers(self, headers: dict):
        """
        Update rate limit info from response headers

        Args:
            headers: Response headers dictionary
        """
        self.rate_limit_remaining = headers.get("x-ratelimit-remaining")
        self.rate_limit_reset = headers.get("x-ratelimit-reset")
        self.rate_limit_limit = headers.get("x-ratelimit-limit")
        self.rate_limit_resource = headers.get("x-ratelimit-resource")

        if self.rate_limit_remaining:
            remaining = int(self.rate_limit_remaining)
            logger.debug(
                f"Rate limit: {remaining}/{self.rate_limit_limit} "
                f"remaining for {self.rate_limit_resource}"
            )

            # Proactive waiting if remaining is low
            if remaining < 10 and self.rate_limit_reset:
                reset_time = int(self.rate_limit_reset)
                current_time = int(time.time())
                wait_time = max(0, reset_time - current_time)

                if wait_time > 0:
                    logger.warning(
                        f"Rate limit low ({remaining} remaining), "
                        f"waiting {wait_time}s until reset"
                    )
                    time.sleep(wait_time + 1)  # Add 1 second buffer

    def handle_rate_limit_error(self, retry_after: Optional[int] = None):
        """
        Handle rate limit error (403/429)

        Args:
            retry_after: Seconds to wait (from Retry-After header)
        """
        if retry_after:
            wait_time = retry_after
        elif self.rate_limit_reset:
            reset_time = int(self.rate_limit_reset)
            current_time = int(time.time())
            wait_time = max(60, reset_time - current_time + 1)
        else:
            wait_time = 60  # Default to 60 seconds

        logger.warning(f"Rate limit exceeded, waiting {wait_time}s")
        time.sleep(wait_time)

    def exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Exponential backoff for retries

        Args:
            attempt: Retry attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = min(base_delay * (2 ** attempt), max_delay)
        logger.debug(f"Exponential backoff: waiting {delay:.2f}s (attempt {attempt + 1})")
        time.sleep(delay)
