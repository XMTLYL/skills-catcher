"""
Task repository (Data Access Object)
"""
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import get_session
from src.models import GitHubScanTask
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskRepository:
    """
    Data access object for GitHubScanTask

    Provides CRUD operations for scan tasks
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

    def create_task(
        self,
        task_type: str,
        query_text: Optional[str] = None
    ) -> GitHubScanTask:
        """
        Create a new scan task

        Args:
            task_type: Task type (code_search/repo_tree/user_submit/update_check)
            query_text: Optional query text or repository address

        Returns:
            GitHubScanTask instance
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            task = GitHubScanTask(
                task_type=task_type,
                query_text=query_text,
                status='pending',
                created_at=datetime.utcnow()
            )

            self.session.add(task)
            self.session.flush()

            logger.info(f"Created task: {task_type} (ID: {task.id})")
            return task

        except Exception as e:
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise

    def start_task(self, task_id: int) -> bool:
        """
        Mark task as running

        Args:
            task_id: Task ID

        Returns:
            True if updated, False otherwise
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            task = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.id == task_id
            ).first()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            task.status = 'running'
            task.started_at = datetime.utcnow()

            self.session.flush()
            logger.info(f"Started task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start task: {e}", exc_info=True)
            return False

    def complete_task(
        self,
        task_id: int,
        total_found: int = 0,
        total_saved: int = 0,
        total_skipped: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Mark task as completed

        Args:
            task_id: Task ID
            total_found: Total found count
            total_saved: Total saved count
            total_skipped: Total skipped count
            error_message: Optional error message

        Returns:
            True if updated, False otherwise
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            task = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.id == task_id
            ).first()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            task.status = 'success' if not error_message else 'failed'
            task.total_found = total_found
            task.total_saved = total_saved
            task.total_skipped = total_skipped
            task.error_message = error_message
            task.finished_at = datetime.utcnow()

            # Calculate total_failed
            task.total_failed = total_found - total_saved - total_skipped

            self.session.flush()
            logger.info(f"Completed task {task_id}: {task.status}")
            return True

        except Exception as e:
            logger.error(f"Failed to complete task: {e}", exc_info=True)
            return False

    def fail_task(self, task_id: int, error_message: str) -> bool:
        """
        Mark task as failed

        Args:
            task_id: Task ID
            error_message: Error message

        Returns:
            True if updated, False otherwise
        """
        return self.complete_task(task_id, error_message=error_message)

    def get_task_stats(self) -> Dict[str, Any]:
        """
        Get task statistics

        Returns:
            Dictionary with task statistics
        """
        if not self.session:
            raise RuntimeError("Repository must be used as context manager")

        try:
            total_tasks = self.session.query(GitHubScanTask).count()

            pending_tasks = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.status == 'pending'
            ).count()

            running_tasks = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.status == 'running'
            ).count()

            success_tasks = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.status == 'success'
            ).count()

            failed_tasks = self.session.query(GitHubScanTask).filter(
                GitHubScanTask.status == 'failed'
            ).count()

            return {
                'total': total_tasks,
                'pending': pending_tasks,
                'running': running_tasks,
                'success': success_tasks,
                'failed': failed_tasks
            }

        except Exception as e:
            logger.error(f"Failed to get task stats: {e}", exc_info=True)
            return {}
