"""
Unit tests for GitHub API client
"""
import pytest
import responses
from src.github.client import GitHubClient
from src.github.exceptions import (
    NotFoundError,
    RateLimitError,
    AuthenticationError,
    NotModifiedError
)


@pytest.fixture
def github_client():
    """Create GitHub client for testing"""
    return GitHubClient(token="test_token")


class TestGitHubClient:
    """Test cases for GitHubClient"""

    @responses.activate
    def test_search_code_success(self, github_client):
        """Test successful code search"""
        responses.add(
            responses.GET,
            "https://api.github.com/search/code",
            json={
                "total_count": 2,
                "items": [
                    {
                        "name": "SKILL.md",
                        "path": "skills/pdf/SKILL.md",
                        "repository": {
                            "full_name": "test/repo",
                            "html_url": "https://github.com/test/repo"
                        }
                    },
                    {
                        "name": "SKILL.md",
                        "path": "skills/browser/SKILL.md",
                        "repository": {
                            "full_name": "test/repo2",
                            "html_url": "https://github.com/test/repo2"
                        }
                    }
                ]
            },
            status=200,
            headers={
                "x-ratelimit-remaining": "30",
                "x-ratelimit-limit": "30",
                "x-ratelimit-reset": "1234567890"
            }
        )

        results = github_client.search_code('filename:SKILL.md "description:"', page=1, per_page=30)

        assert len(results) == 2
        assert results[0]["name"] == "SKILL.md"
        assert results[0]["path"] == "skills/pdf/SKILL.md"

    @responses.activate
    def test_get_file_content_success(self, github_client):
        """Test successful file content retrieval"""
        import base64
        content = "# Test Skill\n\nThis is a test skill."
        encoded_content = base64.b64encode(content.encode()).decode()

        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/contents/SKILL.md",
            json={
                "content": encoded_content,
                "encoding": "base64",
                "sha": "abc123",
                "size": len(content)
            },
            status=200,
            headers={
                "etag": '"abc123"',
                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"
            }
        )

        result = github_client.get_file_content(
            "https://api.github.com/repos/test/repo/contents/SKILL.md"
        )

        assert result["content"] == content
        assert result["sha"] == "abc123"
        assert result["etag"] == '"abc123"'

    @responses.activate
    def test_get_file_content_not_modified(self, github_client):
        """Test 304 Not Modified response"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/contents/SKILL.md",
            status=304,
            headers={
                "etag": '"abc123"',
                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"
            }
        )

        with pytest.raises(NotModifiedError) as exc_info:
            github_client.get_file_content(
                "https://api.github.com/repos/test/repo/contents/SKILL.md",
                etag='"abc123"'
            )

        assert exc_info.value.etag == '"abc123"'

    @responses.activate
    def test_get_file_content_not_found(self, github_client):
        """Test 404 Not Found response"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/contents/SKILL.md",
            status=404,
            json={"message": "Not Found"}
        )

        with pytest.raises(NotFoundError):
            github_client.get_file_content(
                "https://api.github.com/repos/test/repo/contents/SKILL.md"
            )

    @responses.activate
    def test_get_repo_info_success(self, github_client):
        """Test successful repository info retrieval"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo",
            json={
                "stargazers_count": 100,
                "forks_count": 20,
                "watchers_count": 50,
                "open_issues_count": 5,
                "license": {
                    "spdx_id": "MIT"
                },
                "default_branch": "main",
                "archived": False,
                "disabled": False,
                "private": False,
                "updated_at": "2024-01-01T00:00:00Z",
                "pushed_at": "2024-01-01T00:00:00Z"
            },
            status=200
        )

        result = github_client.get_repo_info("test/repo")

        assert result["stars"] == 100
        assert result["forks"] == 20
        assert result["repo_license"] == "MIT"
        assert result["default_branch"] == "main"
        assert result["archived"] is False

    @responses.activate
    def test_rate_limit_error(self, github_client):
        """Test rate limit error handling"""
        responses.add(
            responses.GET,
            "https://api.github.com/search/code",
            status=403,
            json={"message": "API rate limit exceeded"},
            headers={
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "1234567890"
            }
        )

        with pytest.raises(RateLimitError):
            github_client.search_code('filename:SKILL.md', page=1)

    @responses.activate
    def test_authentication_error(self, github_client):
        """Test authentication error handling"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo",
            status=401,
            json={"message": "Bad credentials"}
        )

        with pytest.raises(AuthenticationError):
            github_client.get_repo_info("test/repo")

    @responses.activate
    def test_list_directory_success(self, github_client):
        """Test successful directory listing"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/contents/skills",
            json=[
                {
                    "name": "scripts",
                    "type": "dir"
                },
                {
                    "name": "SKILL.md",
                    "type": "file"
                },
                {
                    "name": "assets",
                    "type": "dir"
                }
            ],
            status=200
        )

        result = github_client.list_directory("test/repo", "skills")

        assert len(result) == 3
        assert result[0]["name"] == "scripts"
        assert result[0]["type"] == "dir"

    @responses.activate
    def test_get_tree_success(self, github_client):
        """Test successful tree retrieval"""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/git/trees/main",
            json={
                "tree": [
                    {
                        "path": "skills/pdf/SKILL.md",
                        "type": "blob"
                    },
                    {
                        "path": "skills/browser/SKILL.md",
                        "type": "blob"
                    },
                    {
                        "path": "README.md",
                        "type": "blob"
                    }
                ]
            },
            status=200
        )

        result = github_client.get_tree("test/repo", "main", recursive=True)

        assert len(result) == 3
        assert result[0]["path"] == "skills/pdf/SKILL.md"
