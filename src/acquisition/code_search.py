"""
Code Search acquisition strategy
"""
import time
from typing import Set

from config import Config
from src.acquisition.base_acquirer import BaseAcquirer, AcquisitionResult
from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector


class CodeSearchAcquirer(BaseAcquirer):
    """
    Acquisition strategy using GitHub Code Search API

    Searches for SKILL.md files across all public repositories
    """

    def __init__(
        self,
        github_client: GitHubClient,
        parser: SkillParser,
        scanner: RiskScanner,
        detector: DirectoryDetector,
        search_queries: list = None,
        max_pages: int = None,
        per_page: int = None
    ):
        """
        Initialize Code Search acquirer

        Args:
            github_client: GitHub API client
            parser: SKILL.md parser
            scanner: Risk scanner
            detector: Directory detector
            search_queries: List of search queries (default from config)
            max_pages: Maximum pages per query (default from config)
            per_page: Results per page (default from config)
        """
        super().__init__(github_client, parser, scanner, detector)

        self.search_queries = search_queries or Config.SEARCH_QUERIES
        self.max_pages = max_pages or Config.MAX_PAGES_PER_QUERY
        self.per_page = per_page or Config.RESULTS_PER_PAGE

    def acquire(self) -> AcquisitionResult:
        """
        Execute Code Search acquisition

        Returns:
            AcquisitionResult with statistics and records
        """
        result = AcquisitionResult()
        seen = set()  # Track processed URLs to avoid duplicates

        self.logger.info(f"Starting Code Search acquisition with {len(self.search_queries)} queries")

        for query_idx, query in enumerate(self.search_queries, 1):
            self.logger.info(f"[{query_idx}/{len(self.search_queries)}] Searching: {query}")

            try:
                self._process_query(query, result, seen)
            except Exception as e:
                self.logger.error(f"Query failed: {query} - {e}", exc_info=True)
                continue

            # Sleep between queries to respect rate limits
            if query_idx < len(self.search_queries):
                self.logger.debug(f"Waiting {Config.CODE_SEARCH_INTERVAL}s before next query")
                time.sleep(Config.CODE_SEARCH_INTERVAL)

        self.logger.info(f"Code Search acquisition completed: {result}")
        return result

    def _process_query(self, query: str, result: AcquisitionResult, seen: Set[str]):
        """
        Process a single search query

        Args:
            query: Search query string
            result: AcquisitionResult to update
            seen: Set of seen URLs for deduplication
        """
        for page in range(1, self.max_pages + 1):
            self.logger.debug(f"Fetching page {page}/{self.max_pages}")

            try:
                items = self.github_client.search_code(query, page=page, per_page=self.per_page)
            except Exception as e:
                self.logger.error(f"Search failed for page {page}: {e}")
                break

            if not items:
                self.logger.debug(f"No more results for query: {query}")
                break

            self.logger.info(f"Processing {len(items)} results from page {page}")

            for idx, item in enumerate(items, 1):
                # Extract item info
                repo = item.get("repository", {})
                repo_full_name = repo.get("full_name")
                repo_url = repo.get("html_url")
                repo_owner = repo.get("owner", {}).get("login")
                default_branch = repo.get("default_branch", "main")

                skill_path = item.get("path")
                skill_html_url = item.get("html_url")
                skill_api_url = item.get("url")

                # Validate required fields
                if not all([repo_full_name, skill_path, skill_api_url]):
                    self.logger.warning(f"Missing required fields in item {idx}")
                    result.add_failed()
                    continue

                # Check for duplicates
                key = skill_html_url or f"{repo_full_name}/{skill_path}"
                if key in seen:
                    self.logger.debug(f"Skipping duplicate: {key}")
                    result.add_skipped()
                    continue

                seen.add(key)
                result.add_found()

                # Progress feedback
                self.logger.info(
                    f"[{result.total_found}/{len(items)}] 正在处理: "
                    f"{repo_full_name}/{skill_path}"
                )

                # Process skill
                try:
                    record = self.process_skill(
                        repo_full_name=repo_full_name,
                        skill_path=skill_path,
                        skill_html_url=skill_html_url,
                        skill_api_url=skill_api_url,
                        repo_owner=repo_owner,
                        repo_url=repo_url,
                        default_branch=default_branch,
                        source_type="github_search"
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

                # Small delay between items
                time.sleep(Config.CONTENTS_API_INTERVAL)

            # Sleep between pages
            if page < self.max_pages:
                time.sleep(2)
