"""
GitHub API client
"""
import base64
import time
from typing import Dict, List, Optional, Any
import requests

from config import Config
from src.github.rate_limiter import RateLimiter
from src.github.exceptions import (
    GitHubAPIError,
    RateLimitError,
    NotFoundError,
    AuthenticationError,
    ServerError,
    NotModifiedError
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """
    GitHub API client with rate limiting and error handling
    """

    def __init__(self, token: str = None, rate_limiter: RateLimiter = None):
        """
        Initialize GitHub API client

        Args:
            token: GitHub Personal Access Token
            rate_limiter: Optional RateLimiter instance
        """
        self.token = token or Config.GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token is required")

        self.base_url = Config.GITHUB_API_BASE
        self.rate_limiter = rate_limiter or RateLimiter(
            code_search_interval=Config.CODE_SEARCH_INTERVAL,
            contents_interval=Config.CONTENTS_API_INTERVAL
        )

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": Config.GITHUB_API_VERSION
        })

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        extra_headers: Optional[Dict] = None,
        resource_type: str = "contents",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            extra_headers: Additional headers
            resource_type: Resource type for rate limiting
            max_retries: Maximum retry attempts

        Returns:
            Response data dictionary

        Raises:
            Various GitHubAPIError subclasses
        """
        headers = dict(self.session.headers)
        if extra_headers:
            headers.update(extra_headers)

        for attempt in range(max_retries):
            try:
                # Rate limiting
                self.rate_limiter.wait_if_needed(resource_type)

                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                # Update rate limit info
                self.rate_limiter.update_from_headers(response.headers)

                # Handle 304 Not Modified
                if response.status_code == 304:
                    raise NotModifiedError(
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified")
                    )

                # Handle 404 Not Found
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}")

                # Handle 401/403 Authentication
                if response.status_code in [401, 403]:
                    # Check if it's rate limit or auth error
                    if "rate limit" in response.text.lower():
                        retry_after = response.headers.get("retry-after")
                        self.rate_limiter.handle_rate_limit_error(
                            int(retry_after) if retry_after else None
                        )
                        if attempt < max_retries - 1:
                            continue
                        raise RateLimitError(
                            "Rate limit exceeded",
                            reset_time=self.rate_limiter.rate_limit_reset
                        )
                    else:
                        raise AuthenticationError(f"Authentication failed: {response.text}")

                # Handle 429 Too Many Requests
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    self.rate_limiter.handle_rate_limit_error(
                        int(retry_after) if retry_after else None
                    )
                    if attempt < max_retries - 1:
                        continue
                    raise RateLimitError("Too many requests")

                # Handle 5xx Server Errors
                if response.status_code >= 500:
                    if attempt < max_retries - 1:
                        self.rate_limiter.exponential_backoff(attempt)
                        continue
                    raise ServerError(f"Server error: {response.status_code}")

                # Raise for other error status codes
                response.raise_for_status()

                # Return successful response
                return {
                    "data": response.json() if response.content else None,
                    "etag": response.headers.get("etag"),
                    "last_modified": response.headers.get("last-modified"),
                    "status_code": response.status_code
                }

            except (requests.RequestException, GitHubAPIError) as e:
                if attempt < max_retries - 1 and not isinstance(e, (NotFoundError, AuthenticationError)):
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    self.rate_limiter.exponential_backoff(attempt)
                    continue
                raise

        raise GitHubAPIError(f"Request failed after {max_retries} attempts")

    def search_code(
        self,
        query: str,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict]:
        """
        Search code using GitHub Code Search API

        Args:
            query: Search query
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of search result items
        """
        logger.info(f"Searching code: query='{query}', page={page}, per_page={per_page}")

        url = f"{self.base_url}/search/code"
        params = {
            "q": query,
            "page": page,
            "per_page": min(per_page, 100)
        }

        try:
            result = self._request("GET", url, params=params, resource_type="code_search")
            items = result["data"].get("items", [])
            logger.info(f"Found {len(items)} results")
            return items

        except NotModifiedError:
            logger.debug("Search results not modified")
            return []

        except Exception as e:
            logger.error(f"Code search failed: {e}")
            raise

    def get_file_content(
        self,
        api_url: str,
        etag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get file content using GitHub Contents API

        Args:
            api_url: GitHub Contents API URL
            etag: Optional ETag for conditional request

        Returns:
            Dictionary with content, sha, size, etag, last_modified

        Raises:
            NotModifiedError: If file has not been modified (304)
        """
        logger.debug(f"Fetching file content: {api_url}")

        extra_headers = {}
        if etag:
            extra_headers["If-None-Match"] = etag

        try:
            result = self._request("GET", api_url, extra_headers=extra_headers)
            data = result["data"]

            # Decode base64 content
            content = ""
            if data.get("encoding") == "base64" and data.get("content"):
                try:
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"Failed to decode content: {e}")

            return {
                "content": content,
                "sha": data.get("sha"),
                "size": data.get("size"),
                "download_url": data.get("download_url"),
                "etag": result.get("etag"),
                "last_modified": result.get("last_modified")
            }

        except NotModifiedError as e:
            logger.debug(f"File not modified: {api_url}")
            raise

    def get_repo_info(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Get repository information

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            Dictionary with repository metadata
        """
        logger.debug(f"Fetching repo info: {repo_full_name}")

        url = f"{self.base_url}/repos/{repo_full_name}"

        try:
            result = self._request("GET", url)
            data = result["data"]

            license_info = data.get("license") or {}

            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "watchers": data.get("watchers_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "repo_license": license_info.get("spdx_id") or "",
                "default_branch": data.get("default_branch") or "main",
                "archived": data.get("archived", False),
                "disabled": data.get("disabled", False),
                "private": data.get("private", False),
                "updated_at": data.get("updated_at"),
                "pushed_at": data.get("pushed_at")
            }

        except Exception as e:
            logger.error(f"Failed to fetch repo info for {repo_full_name}: {e}")
            raise

    def get_tree(
        self,
        repo_full_name: str,
        tree_sha: str,
        recursive: bool = True
    ) -> List[Dict]:
        """
        Get Git tree (directory structure)

        Args:
            repo_full_name: Repository full name (owner/repo)
            tree_sha: Tree SHA or branch name
            recursive: Whether to fetch recursively

        Returns:
            List of tree items
        """
        logger.debug(f"Fetching tree: {repo_full_name} @ {tree_sha}")

        url = f"{self.base_url}/repos/{repo_full_name}/git/trees/{tree_sha}"
        params = {"recursive": "1" if recursive else "0"}

        try:
            result = self._request("GET", url, params=params)
            tree = result["data"].get("tree", [])
            logger.debug(f"Tree contains {len(tree)} items")
            return tree

        except Exception as e:
            logger.error(f"Failed to fetch tree for {repo_full_name}: {e}")
            raise

    def list_directory(
        self,
        repo_full_name: str,
        path: str
    ) -> List[Dict]:
        """
        List directory contents

        Args:
            repo_full_name: Repository full name (owner/repo)
            path: Directory path

        Returns:
            List of directory items
        """
        logger.debug(f"Listing directory: {repo_full_name}/{path}")

        url = f"{self.base_url}/repos/{repo_full_name}/contents/{path}"

        try:
            result = self._request("GET", url)
            data = result["data"]

            if not isinstance(data, list):
                logger.warning(f"Expected list, got {type(data)}")
                return []

            return data

        except Exception as e:
            logger.error(f"Failed to list directory {repo_full_name}/{path}: {e}")
            raise
