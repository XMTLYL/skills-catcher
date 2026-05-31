"""
Unit tests for SkillParser
"""
import pytest
from src.parser.skill_parser import SkillParser


class TestSkillParser:
    """Test cases for SkillParser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return SkillParser()

    def test_parse_with_frontmatter(self, parser):
        """Test parsing SKILL.md with frontmatter"""
        content = """---
name: pdf-processing
description: Read and process PDF files
license: MIT
compatibility: codex
allowed-tools:
  - python
  - file-system
---

# PDF Processing

This skill helps you process PDF files.
"""
        result = parser.parse(content)

        assert result is not None
        assert result["name"] == "pdf-processing"
        assert result["description"] == "Read and process PDF files"
        assert result["license"] == "MIT"
        assert result["compatibility"] == "codex"
        assert result["allowed_tools"] == ["python", "file-system"]

    def test_parse_without_frontmatter(self, parser):
        """Test parsing SKILL.md without frontmatter"""
        content = """# Browser Automation

This skill allows you to automate browser interactions using Playwright.
You can navigate to URLs, click elements, and extract data.
"""
        result = parser.parse(content)

        assert result is not None
        assert result["name"] == "Browser Automation"
        assert "automate browser interactions" in result["description"]

    def test_parse_with_incomplete_frontmatter(self, parser):
        """Test parsing with incomplete frontmatter (fallback)"""
        content = """---
name: test-skill
---

# Test Skill

This is a test skill for unit testing purposes.
"""
        result = parser.parse(content)

        assert result is not None
        assert result["name"] == "test-skill"
        assert "test skill" in result["description"].lower()

    def test_parse_empty_content(self, parser):
        """Test parsing empty content"""
        result = parser.parse("")

        assert result is None

    def test_parse_invalid_yaml(self, parser):
        """Test parsing with invalid YAML frontmatter"""
        content = """---
name: test
invalid: [unclosed
---

# Test

Description here.
"""
        result = parser.parse(content)

        # Should fallback to title extraction
        assert result is not None
        assert result["name"] == "Test"

    def test_parse_long_description(self, parser):
        """Test parsing with long description (should truncate)"""
        long_text = "A" * 500
        content = f"""# Long Skill

{long_text}
"""
        result = parser.parse(content)

        assert result is not None
        assert len(result["description"]) <= 303  # 300 + "..."

    def test_validate_valid_data(self, parser):
        """Test validation with valid data"""
        data = {
            "name": "test-skill",
            "description": "Test description"
        }

        assert parser.validate(data) is True

    def test_validate_missing_name(self, parser):
        """Test validation with missing name"""
        data = {
            "description": "Test description"
        }

        assert parser.validate(data) is False

    def test_validate_missing_description(self, parser):
        """Test validation with missing description"""
        data = {
            "name": "test-skill"
        }

        assert parser.validate(data) is False

    def test_validate_name_too_long(self, parser):
        """Test validation with name too long"""
        data = {
            "name": "A" * 300,
            "description": "Test description"
        }

        assert parser.validate(data) is False

    def test_parse_with_allowed_tools_underscore(self, parser):
        """Test parsing with allowed_tools (underscore variant)"""
        content = """---
name: test-skill
description: Test skill
allowed_tools:
  - bash
  - python
---

# Test
"""
        result = parser.parse(content)

        assert result is not None
        assert result["allowed_tools"] == ["bash", "python"]
