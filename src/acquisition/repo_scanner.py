"""
Repository scanner acquisition strategy
"""
import time
from typing import List, Optional

from config import Config
from src.acquisition.base_acquirer import BaseAcquirer, AcquisitionResult
from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector


class RepoScannerAcquirer(BaseAcquirer):
    """
    Acquisition strategy for scanning specific repositories

    Uses Git Trees API to find all SKILL.md files in a repository
    """

    def __init__(
        self,
        github_client: GitHubClient,
        parser: SkillParser,
        scanner: RiskScanner,
        detector: DirectoryDetector,
        repositories: List[str] = None
    ):
        """
        Initialize Repository Scanner acquirer

        Args:
            github_client: GitHub API client
            parser: SKILL.md parser
            scanner: Risk scanner
            detector: Directory detector
            repositories: List of repository full names (owner/repo)
        """
        super().__init__(github_client, parser, scanner, detector)
        self.repositories = repositories or []

    def acquire(self) -> AcquisitionResult:
        """
        Execute repository scanning acquisition

        Returns:
            AcquisitionResult with statistics and records
        """
        result = AcquisitionResult()

        if not self.repositories:
            self.logger.warning("No repositories provided for scanning")
            return result

        self.logger.info(f"Starting repository scan for {len(self.repositories)} repositories")

        for idx, repo_full_name in enumerate(self.repositories, 1):
            self.logger.info(f"[{idx}/{len(self.repositories)}] Scanning repository: {repo_full_name}")

            try:
                self._scan_repository(repo_full_name, result)
            except Exception as e:
                self.logger.error(f"Failed to scan repository {repo_full_name}: {e}", exc_info=True)
                continue

            # Sleep between repositories
            if idx < len(self.repositories):
                time.sleep(2)

        self.logger.info(f"Repository scan completed: {result}")
        return result

    def _scan_repository(self, repo_full_name: str, result: AcquisitionResult):
        """
        Scan a single repository for SKILL.md files

        Args:
            repo_full_name: Repository full name (owner/repo)
            result: AcquisitionResult to update
        """
        # Step 1: Get repository info
        self.logger.debug(f"Fetching repository info: {repo_full_name}")
        try:
            repo_info = self.github_client.get_repo_info(repo_full_name)
            default_branch = repo_info.get("default_branch", "main")
            repo_owner = repo_full_name.split("/")[0]
            repo_url = f"https://github.com/{repo_full_name}"
        except Exception as e:
            self.logger.error(f"Failed to fetch repo info: {e}")
            return

        # Step 2: Get Git tree
        self.logger.debug(f"Fetching Git tree for branch: {default_branch}")
        try:
            tree_items = self.github_client.get_tree(
                repo_full_name=repo_full_name,
                tree_sha=default_branch,
                recursive=True
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch Git tree: {e}")
            return

        # Step 3: Find all SKILL.md files
        skill_files = [
            item for item in tree_items
            if item.get("path", "").endswith("SKILL.md") and item.get("type") == "blob"
        ]

        if not skill_files:
            self.logger.info(f"No SKILL.md files found in {repo_full_name}")
            return

        self.logger.info(f"Found {len(skill_files)} SKILL.md files in {repo_full_name}")

        # Step 4: Process each SKILL.md file
        for idx, skill_file in enumerate(skill_files, 1):
            skill_path = skill_file.get("path")
            skill_html_url = f"https://github.com/{repo_full_name}/blob/{default_branch}/{skill_path}"
            skill_api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{skill_path}"

            result.add_found()

            # Progress feedback
            self.logger.info(
                f"[{idx}/{len(skill_files)}] 正在处理: "
                f"{repo_full_name}/{skill_path}"
            )

            try:
                record = self.process_skill(
                    repo_full_name=repo_full_name,
                    skill_path=skill_path,
                    skill_html_url=skill_html_url,
                    skill_api_url=skill_api_url,
                    repo_owner=repo_owner,
                    repo_url=repo_url,
                    default_branch=default_branch,
                    source_type="trusted_repo"
                )

                if record:
                    if record.get("not_modified"):
                        result.add_skipped()
                    else:
                        result.add_saved(record)
                else:
                    result.add_failed()

            except Exception as e:
                self.logger.error(f"Failed to process {skill_path}: {e}")
                result.add_failed()

            # Small delay between files
            time.sleep(Config.CONTENTS_API_INTERVAL)
