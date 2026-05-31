"""
Known repository repository (Data Access Object)
"""
from typing import List, Optional
from datetime import datetime

from src.database import get_session
from src.models import GitHubKnownRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KnownRepositoryRepository:
    """
    Data access object for GitHubKnownRepository

    Provides CRUD operations for known repositories
    """

    def __init__(self):
        """Initialize repository"""
        self.session = None

    def __enter__(self):
        """Context manager entry"""
        self.session = get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
            self.session.close()

    def find_all_enabled(self) -> List[GitHubKnownRepository]:
        """
        Find all enabled repositories

        Returns:
            List of GitHubKnownRepository instances
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubKnownRepository).filter(
            GitHubKnownRepository.scan_enabled == 1
        ).all()

    def find_by_full_name(self, repo_full_name: str) -> Optional[GitHubKnownRepository]:
        """
        Find repository by full name

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            GitHubKnownRepository instance or None
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubKnownRepository).filter(
            GitHubKnownRepository.repo_full_name == repo_full_name
        ).first()

    def update_last_scanned(self, repo_full_name: str) -> bool:
        """
        Update last_scanned_at timestamp

        Args:
            repo_full_name: Repository full name

        Returns:
            True if updated, False otherwise
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            repo = self.find_by_full_name(repo_full_name)
            if not repo:
                logger.warning(f"Repository not found: {repo_full_name}")
                return False

            repo.last_scanned_at = datetime.utcnow()
            repo.updated_at = datetime.utcnow()

            self.session.flush()
            logger.info(f"Updated last_scanned for {repo_full_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update last_scanned: {e}", exc_info=True)
            return False
