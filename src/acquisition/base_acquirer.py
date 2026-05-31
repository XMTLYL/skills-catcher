"""
Base acquirer class for all acquisition strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime

from src.github.client import GitHubClient
from src.github.exceptions import NotModifiedError, NotFoundError
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector
from src.utils.helpers import get_skill_dir, build_raw_url
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AcquisitionResult:
    """Result of an acquisition operation"""

    def __init__(self):
        self.total_found = 0
        self.total_saved = 0
        self.total_skipped = 0
        self.total_failed = 0
        self.records = []

    def add_found(self):
        """Increment found count"""
        self.total_found += 1

    def add_saved(self, record: Dict):
        """Add saved record"""
        self.total_saved += 1
        self.records.append(record)

    def add_skipped(self):
        """Increment skipped count"""
        self.total_skipped += 1

    def add_failed(self):
        """Increment failed count"""
        self.total_failed += 1

    def __str__(self):
        return (
            f"发现: {self.total_found}, "
            f"保存: {self.total_saved}, "
            f"跳过: {self.total_skipped}, "
            f"失败: {self.total_failed}"
        )


class BaseAcquirer(ABC):
    """
    Base class for all acquisition strategies

    Provides common processing logic for:
    - Reading SKILL.md content
    - Parsing metadata
    - Fetching repository info
    - Detecting directory structure
    - Risk scanning
    - Building record
    """

    def __init__(
        self,
        github_client: GitHubClient,
        parser: SkillParser,
        scanner: RiskScanner,
        detector: DirectoryDetector
    ):
        """
        Initialize base acquirer

        Args:
            github_client: GitHub API client
            parser: SKILL.md parser
            scanner: Risk scanner
            detector: Directory detector
        """
        self.github_client = github_client
        self.parser = parser
        self.scanner = scanner
        self.detector = detector
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def acquire(self) -> AcquisitionResult:
        """
        Execute acquisition strategy

        Returns:
            AcquisitionResult with statistics and records
        """
        pass

    def process_skill(
        self,
        repo_full_name: str,
        skill_path: str,
        skill_html_url: str,
        skill_api_url: str,
        repo_owner: str,
        repo_url: str,
        default_branch: str = "main",
        etag: Optional[str] = None,
        source_type: str = "github_search"
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single skill file

        Args:
            repo_full_name: Repository full name (owner/repo)
            skill_path: Path to SKILL.md
            skill_html_url: GitHub page URL
            skill_api_url: GitHub Contents API URL
            repo_owner: Repository owner
            repo_url: Repository URL
            default_branch: Default branch name
            etag: Optional ETag for incremental update
            source_type: Source type (github_search/trusted_repo/user_submit)

        Returns:
            Dictionary with skill record, or None if processing fails
        """
        try:
            # Step 1: Fetch file content
            self.logger.debug(f"Fetching content: {skill_path}")
            try:
                file_data = self.github_client.get_file_content(skill_api_url, etag=etag)
            except NotModifiedError as e:
                self.logger.debug(f"File not modified: {skill_path}")
                return {
                    "not_modified": True,
                    "repo_full_name": repo_full_name,
                    "skill_path": skill_path,
                    "etag": e.etag,
                    "last_modified": e.last_modified
                }
            except NotFoundError:
                self.logger.warning(f"File not found: {skill_path}")
                return None

            content = file_data.get("content", "")
            if not content:
                self.logger.warning(f"Empty content: {skill_path}")
                return None

            # Step 2: Parse SKILL.md
            self.logger.debug(f"Parsing SKILL.md: {skill_path}")
            skill_meta = self.parser.parse(content)
            if not skill_meta:
                self.logger.warning(f"Failed to parse: {skill_path}")
                return None

            # Step 3: Fetch repository info
            self.logger.debug(f"Fetching repo info: {repo_full_name}")
            try:
                repo_info = self.github_client.get_repo_info(repo_full_name)
            except Exception as e:
                self.logger.warning(f"Failed to fetch repo info: {e}")
                repo_info = {
                    "stars": 0,
                    "forks": 0,
                    "watchers": 0,
                    "open_issues": 0,
                    "repo_license": "",
                    "default_branch": default_branch,
                    "archived": False,
                    "disabled": False,
                    "private": False,
                    "updated_at": None,
                    "pushed_at": None
                }

            # Update default branch from repo info
            default_branch = repo_info.get("default_branch", default_branch)

            # Step 4: Detect directory structure
            self.logger.debug(f"Detecting directory structure: {skill_path}")
            skill_dir = get_skill_dir(skill_path)
            dir_info = {"has_scripts": False, "has_assets": False, "has_references": False, "has_tests": False}

            if skill_dir:
                try:
                    dir_items = self.github_client.list_directory(repo_full_name, skill_dir)
                    dir_info = self.detector.detect(dir_items)
                except Exception as e:
                    self.logger.debug(f"Failed to detect directory structure: {e}")

            # Step 5: Risk scanning
            self.logger.debug(f"Scanning for risks: {skill_path}")
            risk_level, risk_flags = self.scanner.scan(content, dir_info)

            # Step 6: Build record
            repo_name = repo_full_name.split("/")[1] if "/" in repo_full_name else ""

            record = {
                # Skill metadata
                "name": skill_meta["name"],
                "description": skill_meta["description"],
                "license": skill_meta["license"],
                "compatibility": skill_meta["compatibility"],
                "allowed_tools": skill_meta["allowed_tools"],
                "frontmatter_json": skill_meta["frontmatter"],

                # Repository information
                "repo_full_name": repo_full_name,
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "repo_url": repo_url,
                "repo_default_branch": default_branch,

                # Skill file information
                "skill_path": skill_path,
                "skill_dir": skill_dir,
                "skill_html_url": skill_html_url,
                "skill_raw_url": build_raw_url(repo_full_name, default_branch, skill_path),
                "skill_api_url": skill_api_url,

                # File metadata
                "skill_sha": file_data.get("sha"),
                "skill_size": file_data.get("size"),
                "skill_etag": file_data.get("etag"),
                "skill_last_modified": file_data.get("last_modified"),

                # Repository statistics
                "stars": repo_info.get("stars", 0),
                "forks": repo_info.get("forks", 0),
                "watchers": repo_info.get("watchers", 0),
                "open_issues": repo_info.get("open_issues", 0),
                "repo_license": repo_info.get("repo_license", ""),
                "repo_archived": 1 if repo_info.get("archived") else 0,
                "repo_disabled": 1 if repo_info.get("disabled") else 0,
                "repo_private": 1 if repo_info.get("private") else 0,
                "repo_updated_at": repo_info.get("updated_at"),
                "repo_pushed_at": repo_info.get("pushed_at"),

                # Directory structure
                "has_scripts": 1 if dir_info.get("has_scripts") else 0,
                "has_assets": 1 if dir_info.get("has_assets") else 0,
                "has_references": 1 if dir_info.get("has_references") else 0,
                "has_tests": 1 if dir_info.get("has_tests") else 0,

                # Risk assessment
                "risk_level": risk_level,
                "risk_flags": risk_flags,

                # Source and status
                "source_type": source_type,
                "status": "pending",

                # Timestamps
                "first_found_at": datetime.utcnow(),
                "last_checked_at": datetime.utcnow()
            }

            self.logger.info(
                f"Successfully processed: {skill_meta['name']} "
                f"({repo_full_name}/{skill_path}) - Risk: {risk_level}"
            )

            return record

        except Exception as e:
            self.logger.error(f"Failed to process {skill_path}: {e}", exc_info=True)
            return None
