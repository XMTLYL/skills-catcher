"""
Show statistics script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.skill_repository import SkillRepository
from src.storage.task_repository import TaskRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'stats.log')


def show_stats():
    """Show database statistics"""
    print("\n" + "="*60)
    print("GitHub Skill Indexer - Statistics")
    print("="*60)

    try:
        # Skill statistics
        print("\n📊 Skill Statistics:")
        print("-" * 60)

        with SkillRepository() as skill_repo:
            total_skills = skill_repo.session.query(skill_repo.session.query(skill_repo.session.query.__self__.__class__).count()).scalar()

            # Count by status
            pending = skill_repo.count_by_status('pending')
            approved = skill_repo.count_by_status('approved')
            rejected = skill_repo.count_by_status('rejected')
            risky = skill_repo.count_by_status('risky')
            offline = skill_repo.count_by_status('offline')

            # Get some sample skills
            from src.models import GitHubSkill
            recent_skills = skill_repo.session.query(GitHubSkill).order_by(
                GitHubSkill.created_at.desc()
            ).limit(5).all()

        print(f"Total Skills: {pending + approved + rejected + risky + offline}")
        print(f"  - Pending:  {pending}")
        print(f"  - Approved: {approved}")
        print(f"  - Rejected: {rejected}")
        print(f"  - Risky:    {risky}")
        print(f"  - Offline:  {offline}")

        # Task statistics
        print("\n📋 Task Statistics:")
        print("-" * 60)

        with TaskRepository() as task_repo:
            task_stats = task_repo.get_task_stats()

        print(f"Total Tasks: {task_stats.get('total', 0)}")
        print(f"  - Pending:  {task_stats.get('pending', 0)}")
        print(f"  - Running:  {task_stats.get('running', 0)}")
        print(f"  - Success:  {task_stats.get('success', 0)}")
        print(f"  - Failed:   {task_stats.get('failed', 0)}")

        # Recent skills
        if recent_skills:
            print("\n🆕 Recent Skills:")
            print("-" * 60)
            for i, skill in enumerate(recent_skills, 1):
                print(f"{i}. {skill.name}")
                print(f"   Repo: {skill.repo_full_name}")
                print(f"   Stars: {skill.stars} | Risk: {skill.risk_level} | Status: {skill.status}")
                print()

        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Failed to show stats: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    show_stats()
