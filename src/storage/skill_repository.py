"""
Skill repository (Data Access Object)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.dialects.mysql import insert

from src.database import get_session
from src.models import GitHubSkill
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SkillRepository:
    """
    Data access object for GitHubSkill

    Provides CRUD operations and queries
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

    def upsert(self, skill_data: Dict[str, Any]) -> GitHubSkill:
        """
        Insert or update skill record

        Uses MySQL's INSERT ... ON DUPLICATE KEY UPDATE

        Args:
            skill_data: Skill data dictionary

        Returns:
            GitHubSkill instance
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            # Prepare data for insert
            insert_data = self._prepare_insert_data(skill_data)

            # Build insert statement with ON DUPLICATE KEY UPDATE
            stmt = insert(GitHubSkill).values(**insert_data)

            # Update fields on duplicate key
            update_data = {
                key: value for key, value in insert_data.items()
                if key not in ['repo_full_name', 'skill_path', 'first_found_at']
            }
            update_data['updated_at'] = datetime.utcnow()

            stmt = stmt.on_duplicate_key_update(**update_data)

            # Execute
            self.session.execute(stmt)
            self.session.flush()

            # Fetch the record
            skill = self.find_by_repo_and_path(
                skill_data['repo_full_name'],
                skill_data['skill_path']
            )

            logger.info(
                f"Upserted skill: {skill_data['name']} "
                f"({skill_data['repo_full_name']}/{skill_data['skill_path']})"
            )

            return skill

        except Exception as e:
            logger.error(f"Failed to upsert skill: {e}", exc_info=True)
            raise

    def find_by_repo_and_path(
        self,
        repo_full_name: str,
        skill_path: str
    ) -> Optional[GitHubSkill]:
        """
        Find skill by repository and path

        Args:
            repo_full_name: Repository full name
            skill_path: Skill path

        Returns:
            GitHubSkill instance or None
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubSkill).filter(
            and_(
                GitHubSkill.repo_full_name == repo_full_name,
                GitHubSkill.skill_path == skill_path
            )
        ).first()

    def find_by_id(self, skill_id: int) -> Optional[GitHubSkill]:
        """
        Find skill by ID

        Args:
            skill_id: Skill ID

        Returns:
            GitHubSkill instance or None
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubSkill).filter(
            GitHubSkill.id == skill_id
        ).first()

    def find_pending(self, limit: int = 100) -> List[GitHubSkill]:
        """
        Find pending skills (status = 'pending')

        Args:
            limit: Maximum number of records

        Returns:
            List of GitHubSkill instances
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubSkill).filter(
            GitHubSkill.status == 'pending'
        ).order_by(GitHubSkill.created_at.desc()).limit(limit).all()

    def find_for_update_check(self, limit: int = 100) -> List[GitHubSkill]:
        """
        Find skills that need update check

        Prioritizes:
        - Older last_checked_at
        - Status = 'approved'

        Args:
            limit: Maximum number of records

        Returns:
            List of GitHubSkill instances
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubSkill).filter(
            GitHubSkill.status == 'approved'
        ).order_by(
            GitHubSkill.last_checked_at.asc().nullsfirst()
        ).limit(limit).all()

    def update_status(self, skill_id: int, status: str) -> bool:
        """
        Update skill status

        Args:
            skill_id: Skill ID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            skill = self.find_by_id(skill_id)
            if not skill:
                logger.warning(f"Skill not found: {skill_id}")
                return False

            skill.status = status
            skill.updated_at = datetime.utcnow()

            self.session.flush()
            logger.info(f"Updated skill {skill_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update status: {e}", exc_info=True)
            return False

    def mark_offline(self, skill_id: int) -> bool:
        """
        Mark skill as offline

        Args:
            skill_id: Skill ID

        Returns:
            True if updated, False otherwise
        """
        return self.update_status(skill_id, 'offline')

    def update_last_checked(self, skill_id: int) -> bool:
        """
        Update last_checked_at timestamp

        Args:
            skill_id: Skill ID

        Returns:
            True if updated, False otherwise
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            skill = self.find_by_id(skill_id)
            if not skill:
                return False

            skill.last_checked_at = datetime.utcnow()
            skill.updated_at = datetime.utcnow()

            self.session.flush()
            return True

        except Exception as e:
            logger.error(f"Failed to update last_checked: {e}", exc_info=True)
            return False

    def count_by_status(self, status: str) -> int:
        """
        Count skills by status

        Args:
            status: Status to count

        Returns:
            Count
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        return self.session.query(GitHubSkill).filter(
            GitHubSkill.status == status
        ).count()

    def _prepare_insert_data(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for database insert

        Converts Python types to database types

        Args:
            skill_data: Skill data dictionary

        Returns:
            Prepared data dictionary
        """
        # Convert allowed_tools to JSON-compatible format
        allowed_tools = skill_data.get('allowed_tools')
        if isinstance(allowed_tools, list):
            allowed_tools = ','.join(allowed_tools)

        # Convert risk_flags to JSON
        risk_flags = skill_data.get('risk_flags', [])

        # Convert frontmatter to JSON
        frontmatter_json = skill_data.get('frontmatter_json', {})

        return {
            'name': skill_data.get('name'),
            'description': skill_data.get('description'),
            'slug': skill_data.get('slug'),
            'repo_full_name': skill_data.get('repo_full_name'),
            'repo_owner': skill_data.get('repo_owner'),
            'repo_name': skill_data.get('repo_name'),
            'repo_url': skill_data.get('repo_url'),
            'repo_default_branch': skill_data.get('repo_default_branch'),
            'skill_path': skill_data.get('skill_path'),
            'skill_dir': skill_data.get('skill_dir'),
            'skill_html_url': skill_data.get('skill_html_url'),
            'skill_raw_url': skill_data.get('skill_raw_url'),
            'skill_api_url': skill_data.get('skill_api_url'),
            'skill_sha': skill_data.get('skill_sha'),
            'skill_size': skill_data.get('skill_size'),
            'skill_etag': skill_data.get('skill_etag'),
            'skill_last_modified': skill_data.get('skill_last_modified'),
            'frontmatter_json': frontmatter_json,
            'license': skill_data.get('license'),
            'compatibility': skill_data.get('compatibility'),
            'allowed_tools': allowed_tools,
            'stars': skill_data.get('stars', 0),
            'forks': skill_data.get('forks', 0),
            'watchers': skill_data.get('watchers', 0),
            'open_issues': skill_data.get('open_issues', 0),
            'repo_license': skill_data.get('repo_license'),
            'repo_archived': skill_data.get('repo_archived', 0),
            'repo_disabled': skill_data.get('repo_disabled', 0),
            'repo_private': skill_data.get('repo_private', 0),
            'repo_updated_at': skill_data.get('repo_updated_at'),
            'repo_pushed_at': skill_data.get('repo_pushed_at'),
            'has_scripts': skill_data.get('has_scripts', 0),
            'has_assets': skill_data.get('has_assets', 0),
            'has_references': skill_data.get('has_references', 0),
            'has_tests': skill_data.get('has_tests', 0),
            'risk_level': skill_data.get('risk_level', 'unknown'),
            'risk_flags': risk_flags,
            'license_status': skill_data.get('license_status', 'unknown'),
            'source_type': skill_data.get('source_type', 'github_search'),
            'status': skill_data.get('status', 'pending'),
            'first_found_at': skill_data.get('first_found_at', datetime.utcnow()),
            'last_checked_at': skill_data.get('last_checked_at', datetime.utcnow())
        }
