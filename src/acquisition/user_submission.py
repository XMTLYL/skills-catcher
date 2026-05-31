"""
User submission acquisition strategy
"""
from typing import Optional

from src.acquisition.base_acquirer import BaseAcquirer, AcquisitionResult
from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.parser.url_parser import URLParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector


class UserSubmissionAcquirer(BaseAcquirer):
    """
    Acquisition strategy for user-submitted repositories

    Processes GitHub URLs submitted by users
    """

    def __init__(
        self,
        github_client: GitHubClient,
        parser: SkillParser,
        scanner: RiskScanner,
        detector: DirectoryDetector,
        url_parser: URLParser = None
    ):
        """
        Initialize User Submission acquirer

        Args:
            github_client: GitHub API client
            parser: SKILL.md parser
            scanner: Risk scanner
            detector: Directory detector
            url_parser: URL parser (optional)
        """
        super().__init__(github_client, parser, scanner, detector)
        self.url_parser = url_parser or URLParser()

    def acquire(self, github_url: str, skill_path: Optional[str] = None) -> AcquisitionResult:
        """
        Execute user submission acquisition

        Args:
            github_url: GitHub repository URL or owner/repo
            skill_path: Optional specific path to SKILL.md

        Returns:
            AcquisitionResult with statistics and records
        """
        result = AcquisitionResult()

        self.logger.info(f"Processing user submission: {github_url}")

        # Step 1: Parse URL
        parsed = self.url_parser.parse(github_url)
        if not parsed:
            self.logger.error(f"Failed to parse GitHub URL: {github_url}")
            result.add_failed()
            return result

        repo_full_name = self.url_parser.build_repo_full_name(parsed)
        repo_owner = parsed["owner"]
        repo_url = f"https://github.com/{repo_full_name}"

        # Step 2: Verify repository exists
        self.logger.debug(f"Verifying repository: {repo_full_name}")
        try:
            repo_info = self.github_client.get_repo_info(repo_full_name)
            default_branch = repo_info.get("default_branch", "main")
        except Exception as e:
            self.logger.error(f"Repository not found or inaccessible: {e}")
            result.add_failed()
            return result

        # Step 3: Determine skill path
        if skill_path:
            # User provided specific path
            self.logger.info(f"Using user-provided path: {skill_path}")
            self._process_specific_path(
                repo_full_name, skill_path, repo_owner, repo_url, default_branch, result
            )
        elif parsed.get("skill_path"):
            # URL contains path
            skill_path = parsed["skill_path"]
            self.logger.info(f"Using path from URL: {skill_path}")
            self._process_specific_path(
                repo_full_name, skill_path, repo_owner, repo_url, default_branch, result
            )
        else:
            # Scan entire repository
            self.logger.info(f"No path provided, scanning entire repository")
            self._scan_repository(
                repo_full_name, repo_owner, repo_url, default_branch, result
            )

        self.logger.info(f"User submission processing completed: {result}")
        return result

    def _process_specific_path(
        self,
        repo_full_name: str,
        skill_path: str,
        repo_owner: str,
        repo_url: str,
        default_branch: str,
        result: AcquisitionResult
    ):
        """
        Process a specific SKILL.md path

        Args:
            repo_full_name: Repository full name
            skill_path: Path to SKILL.md
            repo_owner: Repository owner
            repo_url: Repository URL
            default_branch: Default branch
            result: AcquisitionResult to update
        """
        # Ensure path ends with SKILL.md
        if not self.url_parser.is_skill_file(skill_path):
            self.logger.warning(f"Path does not point to SKILL.md: {skill_path}")
            result.add_failed()
            return

        skill_html_url = f"https://github.com/{repo_full_name}/blob/{default_branch}/{skill_path}"
        skill_api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{skill_path}"

        result.add_found()

        self.logger.info(f"正在处理: {repo_full_name}/{skill_path}")

        try:
            record = self.process_skill(
                repo_full_name=repo_full_name,
                skill_path=skill_path,
                skill_html_url=skill_html_url,
                skill_api_url=skill_api_url,
                repo_owner=repo_owner,
                repo_url=repo_url,
                default_branch=default_branch,
                source_type="user_submit"
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

    def _scan_repository(
        self,
        repo_full_name: str,
        repo_owner: str,
        repo_url: str,
        default_branch: str,
        result: AcquisitionResult
    ):
        """
        Scan entire repository for SKILL.md files

        Args:
            repo_full_name: Repository full name
            repo_owner: Repository owner
            repo_url: Repository URL
            default_branch: Default branch
            result: AcquisitionResult to update
        """
        # Get Git tree
        self.logger.debug(f"Fetching Git tree for: {repo_full_name}")
        try:
            tree_items = self.github_client.get_tree(
                repo_full_name=repo_full_name,
                tree_sha=default_branch,
                recursive=True
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch Git tree: {e}")
            result.add_failed()
            return

        # Find all SKILL.md files
        skill_files = [
            item for item in tree_items
            if item.get("path", "").endswith("SKILL.md") and item.get("type") == "blob"
        ]

        if not skill_files:
            self.logger.warning(f"No SKILL.md files found in {repo_full_name}")
            return

        self.logger.info(f"Found {len(skill_files)} SKILL.md files")

        # Process each file
        for idx, skill_file in enumerate(skill_files, 1):
            skill_path = skill_file.get("path")
            skill_html_url = f"https://github.com/{repo_full_name}/blob/{default_branch}/{skill_path}"
            skill_api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{skill_path}"

            result.add_found()

            self.logger.info(f"[{idx}/{len(skill_files)}] 正在处理: {skill_path}")

            try:
                record = self.process_skill(
                    repo_full_name=repo_full_name,
                    skill_path=skill_path,
                    skill_html_url=skill_html_url,
                    skill_api_url=skill_api_url,
                    repo_owner=repo_owner,
                    repo_url=repo_url,
                    default_branch=default_branch,
                    source_type="user_submit"
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
