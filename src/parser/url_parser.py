"""
GitHub URL parser
"""
import re
from typing import Optional, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)


class URLParser:
    """
    Parser for GitHub URLs

    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch/path
    - https://github.com/owner/repo/blob/branch/path/SKILL.md
    - owner/repo
    """

    def parse(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse GitHub URL

        Args:
            url: GitHub URL or owner/repo string

        Returns:
            Dictionary with owner, repo, branch, skill_path
        """
        if not url or not url.strip():
            logger.warning("Empty URL provided")
            return None

        url = url.strip()

        # Pattern 1: owner/repo (simple format)
        if "/" in url and "github.com" not in url and url.count("/") == 1:
            parts = url.split("/")
            return {
                "owner": parts[0],
                "repo": parts[1],
                "branch": None,
                "skill_path": None
            }

        # Pattern 2: Full GitHub URLs
        # https://github.com/owner/repo
        # https://github.com/owner/repo/tree/branch/path
        # https://github.com/owner/repo/blob/branch/path/file.md

        # Extract owner and repo
        match = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)(?:/(.+))?",
            url
        )

        if not match:
            logger.warning(f"Failed to parse GitHub URL: {url}")
            return None

        owner = match.group(1)
        repo = match.group(2)
        rest = match.group(3) or ""

        result = {
            "owner": owner,
            "repo": repo,
            "branch": None,
            "skill_path": None
        }

        # Parse tree/blob paths
        if rest:
            # Pattern: tree/branch/path or blob/branch/path
            tree_match = re.match(r"(tree|blob)/([^/]+)/(.+)", rest)
            if tree_match:
                result["branch"] = tree_match.group(2)
                result["skill_path"] = tree_match.group(3)

        logger.debug(f"Parsed URL: {result}")
        return result

    def build_repo_full_name(self, parsed: Dict[str, str]) -> str:
        """
        Build repository full name from parsed data

        Args:
            parsed: Parsed URL data

        Returns:
            Repository full name (owner/repo)
        """
        if not parsed or not parsed.get("owner") or not parsed.get("repo"):
            return ""

        return f"{parsed['owner']}/{parsed['repo']}"

    def is_skill_file(self, path: str) -> bool:
        """
        Check if path points to a SKILL.md file

        Args:
            path: File path

        Returns:
            True if path ends with SKILL.md
        """
        if not path:
            return False

        return path.endswith("SKILL.md") or path.endswith("skill.md")
