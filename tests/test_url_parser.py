"""
Unit tests for URLParser
"""
import pytest
from src.parser.url_parser import URLParser


class TestURLParser:
    """Test cases for URLParser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return URLParser()

    def test_parse_simple_format(self, parser):
        """Test parsing simple owner/repo format"""
        result = parser.parse("openai/skills")

        assert result is not None
        assert result["owner"] == "openai"
        assert result["repo"] == "skills"
        assert result["branch"] is None
        assert result["skill_path"] is None

    def test_parse_basic_url(self, parser):
        """Test parsing basic GitHub URL"""
        result = parser.parse("https://github.com/anthropics/anthropic-quickstarts")

        assert result is not None
        assert result["owner"] == "anthropics"
        assert result["repo"] == "anthropic-quickstarts"
        assert result["branch"] is None
        assert result["skill_path"] is None

    def test_parse_tree_url(self, parser):
        """Test parsing tree URL with path"""
        result = parser.parse("https://github.com/openai/skills/tree/main/skills/pdf-processing")

        assert result is not None
        assert result["owner"] == "openai"
        assert result["repo"] == "skills"
        assert result["branch"] == "main"
        assert result["skill_path"] == "skills/pdf-processing"

    def test_parse_blob_url(self, parser):
        """Test parsing blob URL with file"""
        result = parser.parse("https://github.com/openai/skills/blob/main/skills/pdf/SKILL.md")

        assert result is not None
        assert result["owner"] == "openai"
        assert result["repo"] == "skills"
        assert result["branch"] == "main"
        assert result["skill_path"] == "skills/pdf/SKILL.md"

    def test_parse_empty_url(self, parser):
        """Test parsing empty URL"""
        result = parser.parse("")

        assert result is None

    def test_parse_invalid_url(self, parser):
        """Test parsing invalid URL"""
        result = parser.parse("not-a-valid-url")

        assert result is None

    def test_build_repo_full_name(self, parser):
        """Test building repository full name"""
        parsed = {
            "owner": "openai",
            "repo": "skills",
            "branch": "main",
            "skill_path": "skills/pdf/SKILL.md"
        }

        full_name = parser.build_repo_full_name(parsed)

        assert full_name == "openai/skills"

    def test_build_repo_full_name_incomplete(self, parser):
        """Test building repository full name with incomplete data"""
        parsed = {
            "owner": "openai"
        }

        full_name = parser.build_repo_full_name(parsed)

        assert full_name == ""

    def test_is_skill_file_true(self, parser):
        """Test checking if path is SKILL.md"""
        assert parser.is_skill_file("skills/pdf/SKILL.md") is True
        assert parser.is_skill_file("SKILL.md") is True
        assert parser.is_skill_file("path/to/skill.md") is True

    def test_is_skill_file_false(self, parser):
        """Test checking if path is not SKILL.md"""
        assert parser.is_skill_file("README.md") is False
        assert parser.is_skill_file("skills/pdf/script.py") is False
        assert parser.is_skill_file("") is False

    def test_parse_http_url(self, parser):
        """Test parsing HTTP URL (should work)"""
        result = parser.parse("http://github.com/test/repo")

        assert result is not None
        assert result["owner"] == "test"
        assert result["repo"] == "repo"
