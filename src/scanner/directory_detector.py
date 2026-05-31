"""
Directory structure detector
"""
from typing import Dict, List
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DirectoryDetector:
    """
    Detector for skill directory structure

    Detects:
    - scripts/
    - assets/
    - references/
    - tests/
    """

    def detect(self, directory_items: List[Dict]) -> Dict[str, bool]:
        """
        Detect directory structure from directory listing

        Args:
            directory_items: List of directory items from GitHub API

        Returns:
            Dictionary with has_scripts, has_assets, has_references, has_tests
        """
        if not directory_items:
            logger.debug("No directory items provided")
            return self._empty_result()

        # Extract directory names
        dir_names = set()
        for item in directory_items:
            if item.get("type") == "dir":
                dir_names.add(item.get("name", "").lower())

        result = {
            "has_scripts": "scripts" in dir_names,
            "has_assets": "assets" in dir_names,
            "has_references": "references" in dir_names,
            "has_tests": "tests" in dir_names or "test" in dir_names
        }

        logger.debug(f"Directory detection result: {result}")
        return result

    def detect_from_tree(self, tree_items: List[Dict], skill_dir: str) -> Dict[str, bool]:
        """
        Detect directory structure from Git tree

        Args:
            tree_items: List of tree items from GitHub Git Trees API
            skill_dir: Skill directory path (e.g., "skills/pdf-processing")

        Returns:
            Dictionary with has_scripts, has_assets, has_references, has_tests
        """
        if not tree_items or not skill_dir:
            logger.debug("No tree items or skill_dir provided")
            return self._empty_result()

        # Normalize skill_dir
        skill_dir = skill_dir.rstrip("/")

        # Find items under skill_dir
        dir_names = set()
        for item in tree_items:
            path = item.get("path", "")

            # Check if path is under skill_dir
            if path.startswith(skill_dir + "/"):
                # Get relative path
                relative_path = path[len(skill_dir) + 1:]

                # Get first directory component
                if "/" in relative_path:
                    first_dir = relative_path.split("/")[0].lower()
                    dir_names.add(first_dir)

        result = {
            "has_scripts": "scripts" in dir_names,
            "has_assets": "assets" in dir_names,
            "has_references": "references" in dir_names,
            "has_tests": "tests" in dir_names or "test" in dir_names
        }

        logger.debug(f"Tree detection result for {skill_dir}: {result}")
        return result

    def _empty_result(self) -> Dict[str, bool]:
        """
        Return empty detection result

        Returns:
            Dictionary with all False values
        """
        return {
            "has_scripts": False,
            "has_assets": False,
            "has_references": False,
            "has_tests": False
        }
