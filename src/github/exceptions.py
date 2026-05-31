"""
Custom exceptions for GitHub API operations
"""


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors"""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, reset_time: int = None):
        super().__init__(message)
        self.reset_time = reset_time


class NotFoundError(GitHubAPIError):
    """Raised when resource is not found (404)"""
    pass


class AuthenticationError(GitHubAPIError):
    """Raised when authentication fails"""
    pass


class ServerError(GitHubAPIError):
    """Raised when server returns 5xx error"""
    pass


class NotModifiedError(GitHubAPIError):
    """Raised when resource has not been modified (304)"""
    def __init__(self, etag: str = None, last_modified: str = None):
        super().__init__("Resource not modified")
        self.etag = etag
        self.last_modified = last_modified
