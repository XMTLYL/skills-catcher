"""
SKILL.md parser
"""
import re
from typing import Optional, Dict, Any
import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SkillParser:
    """
    Parser for SKILL.md files

    Supports:
    - YAML frontmatter parsing
    - Fallback parsing (extract from title and body)
    - Field validation
    """

    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse SKILL.md content

        Args:
            content: SKILL.md file content

        Returns:
            Dictionary with parsed metadata, or None if parsing fails
        """
        if not content or not content.strip():
            logger.warning("Empty content provided")
            return None

        # Try to parse frontmatter
        meta = self._parse_frontmatter(content)

        # Extract fields
        name = meta.get("name")
        description = meta.get("description")

        # Fallback: extract from content if frontmatter is missing
        if not name or not description:
            logger.debug("Frontmatter incomplete, using fallback parsing")
            fallback = self._fallback_parse(content)

            if not name:
                name = fallback.get("name")
            if not description:
                description = fallback.get("description")

        # Validate required fields
        if not name or not description:
            logger.warning("Failed to extract required fields (name, description)")
            return None

        # Build result
        result = {
            "name": str(name).strip(),
            "description": str(description).strip(),
            "license": str(meta.get("license", "")).strip() if meta.get("license") else "",
            "compatibility": str(meta.get("compatibility", "")).strip() if meta.get("compatibility") else "",
            "allowed_tools": meta.get("allowed-tools") or meta.get("allowed_tools") or "",
            "frontmatter": meta
        }

        logger.debug(f"Successfully parsed skill: {result['name']}")
        return result

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter from content

        Args:
            content: File content

        Returns:
            Dictionary with frontmatter data
        """
        # Match frontmatter pattern: ---\n...\n---
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

        if not match:
            logger.debug("No frontmatter found")
            return {}

        frontmatter_text = match.group(1)

        try:
            meta = yaml.safe_load(frontmatter_text)
            if not isinstance(meta, dict):
                logger.warning(f"Frontmatter is not a dictionary: {type(meta)}")
                return {}
            return meta

        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            return {}

    def _fallback_parse(self, content: str) -> Dict[str, Any]:
        """
        Fallback parsing when frontmatter is missing or incomplete

        Extracts:
        - name from first heading (# Title)
        - description from first 300 characters of body

        Args:
            content: File content

        Returns:
            Dictionary with extracted fields
        """
        result = {}

        # Remove frontmatter if present
        content_without_frontmatter = re.sub(
            r"^---\s*\n.*?\n---\s*\n",
            "",
            content,
            flags=re.DOTALL
        )

        # Extract name from first heading
        title_match = re.search(r"^#\s+(.+)$", content_without_frontmatter, re.MULTILINE)
        if title_match:
            result["name"] = title_match.group(1).strip()
            logger.debug(f"Extracted name from heading: {result['name']}")

        # Extract description from body
        # Remove all headings and get first paragraph
        body = re.sub(r"^#+\s+.+$", "", content_without_frontmatter, flags=re.MULTILINE)
        body = body.strip()

        if body:
            # Get first 300 characters, break at word boundary
            description = body.replace("\n", " ")
            description = re.sub(r"\s+", " ", description)  # Normalize whitespace

            if len(description) > 300:
                description = description[:300].rsplit(" ", 1)[0] + "..."

            result["description"] = description
            logger.debug(f"Extracted description: {description[:50]}...")

        return result

    def validate(self, parsed_data: Dict[str, Any]) -> bool:
        """
        Validate parsed data

        Args:
            parsed_data: Parsed skill data

        Returns:
            True if valid, False otherwise
        """
        if not parsed_data:
            return False

        # Check required fields
        if not parsed_data.get("name"):
            logger.warning("Validation failed: name is missing")
            return False

        if not parsed_data.get("description"):
            logger.warning("Validation failed: description is missing")
            return False

        # Check field lengths
        if len(parsed_data["name"]) > 255:
            logger.warning("Validation failed: name too long")
            return False

        return True
