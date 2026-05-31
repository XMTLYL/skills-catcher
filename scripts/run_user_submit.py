"""
User submission processing script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.parser.url_parser import URLParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector
from src.acquisition.user_submission import UserSubmissionAcquirer
from src.storage.skill_repository import SkillRepository
from src.storage.task_repository import TaskRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'user_submit.log')


def run_user_submit(github_url: str, skill_path: str = None):
    """
    Run user submission processing

    Args:
        github_url: GitHub repository URL or owner/repo
        skill_path: Optional specific path to SKILL.md
    """
    logger.info("="*60)
    logger.info("Starting User Submission Processing")
    logger.info("="*60)

    task_id = None

    try:
        # Create task record
        with TaskRepository() as task_repo:
            task = task_repo.create_task(
                task_type='user_submit',
                query_text=github_url
            )
            task_id = task.id
            task_repo.start_task(task_id)

        logger.info(f"Created task ID: {task_id}")

        # Initialize components
        logger.info("Initializing components...")
        github_client = GitHubClient()
        parser = SkillParser()
        url_parser = URLParser()
        scanner = RiskScanner()
        detector = DirectoryDetector()

        # Create acquirer
        acquirer = UserSubmissionAcquirer(
            github_client=github_client,
            parser=parser,
            scanner=scanner,
            detector=detector,
            url_parser=url_parser
        )

        # Execute acquisition
        logger.info(f"Processing submission: {github_url}")
        if skill_path:
            logger.info(f"Specific path: {skill_path}")

        result = acquirer.acquire(github_url, skill_path)

        # Save records to database
        logger.info(f"Saving {len(result.records)} records to database...")
        saved_count = 0

        with SkillRepository() as skill_repo:
            for record in result.records:
                try:
                    if record.get('not_modified'):
                        continue

                    skill_repo.upsert(record)
                    saved_count += 1

                except Exception as e:
                    logger.error(f"Failed to save record: {e}")

        logger.info(f"Successfully saved {saved_count} records to database")

        # Update task status
        with TaskRepository() as task_repo:
            task_repo.complete_task(
                task_id=task_id,
                total_found=result.total_found,
                total_saved=saved_count,
                total_skipped=result.total_skipped
            )

        # Print summary
        print("\n" + "="*60)
        print("✅ User Submission Processing Completed")
        print("="*60)
        print(f"发现: {result.total_found}")
        print(f"保存到数据库: {saved_count}")
        print(f"跳过: {result.total_skipped}")
        print(f"失败: {result.total_failed}")
        print("="*60)

        # Print records
        if result.records:
            print("\n处理结果:")
            for i, record in enumerate(result.records, 1):
                if record.get('not_modified'):
                    continue
                print(f"\n{i}. {record['name']}")
                print(f"   仓库: {record['repo_full_name']}")
                print(f"   路径: {record['skill_path']}")
                print(f"   Stars: {record['stars']}")
                print(f"   风险: {record['risk_level']}")

        logger.info(f"Processing completed: {result}")

    except Exception as e:
        logger.error(f"User submission processing failed: {e}", exc_info=True)

        # Mark task as failed
        if task_id:
            try:
                with TaskRepository() as task_repo:
                    task_repo.fail_task(task_id, str(e))
            except:
                pass

        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_user_submit.py <github_url> [skill_path]")
        print("\nExamples:")
        print("  python run_user_submit.py openai/skills")
        print("  python run_user_submit.py https://github.com/openai/skills")
        print("  python run_user_submit.py openai/skills skills/pdf/SKILL.md")
        sys.exit(1)

    url = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else None

    run_user_submit(url, path)
