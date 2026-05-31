"""
Helper utility functions
"""
from typing import Optional


def get_skill_dir(skill_path: str) -> str:
    """
    Extract skill directory from skill path

    Args:
        skill_path: Path to SKILL.md (e.g., "skills/pdf-processing/SKILL.md")

    Returns:
        Skill directory (e.g., "skills/pdf-processing")
    """
    if "/" not in skill_path:
        return ""
    return skill_path.rsplit("/", 1)[0]


def build_raw_url(repo_full_name: str, branch: str, path: str) -> str:
    """
    Build raw GitHub URL

    Args:
        repo_full_name: Repository full name (owner/repo)
        branch: Branch name
        path: File path

    Returns:
        Raw URL (e.g., https://raw.githubusercontent.com/owner/repo/main/path)
    """
    return f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/{path}"


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug

    Args:
        text: Input text

    Returns:
        Slugified text
    """
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def truncate_text(text: str, max_length: int = 300) -> str:
    """
    Truncate text to maximum length

    Args:
        text: Input text
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
