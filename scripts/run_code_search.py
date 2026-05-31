"""
Code Search acquisition script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector
from src.acquisition.code_search import CodeSearchAcquirer
from src.storage.skill_repository import SkillRepository
from src.storage.task_repository import TaskRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'code_search.log')


def run_code_search():
    """Run Code Search acquisition"""
    logger.info("="*60)
    logger.info("Starting Code Search Acquisition")
    logger.info("="*60)

    task_id = None

    try:
        # Create task record
        with TaskRepository() as task_repo:
            task = task_repo.create_task(
                task_type='code_search',
                query_text='Multiple queries'
            )
            task_id = task.id
            task_repo.start_task(task_id)

        logger.info(f"Created task ID: {task_id}")

        # Initialize components
        logger.info("Initializing components...")
        github_client = GitHubClient()
        parser = SkillParser()
        scanner = RiskScanner()
        detector = DirectoryDetector()

        # Create acquirer
        acquirer = CodeSearchAcquirer(
            github_client=github_client,
            parser=parser,
            scanner=scanner,
            detector=detector
        )

        # Execute acquisition
        logger.info("Starting acquisition...")
        result = acquirer.acquire()

        # Save records to database
        logger.info(f"Saving {len(result.records)} records to database...")
        saved_count = 0

        with SkillRepository() as skill_repo:
            for idx, record in enumerate(result.records, 1):
                try:
                    # Skip not_modified records
                    if record.get('not_modified'):
                        continue

                    skill_repo.upsert(record)
                    saved_count += 1

                    if idx % 10 == 0:
                        logger.info(f"Saved {idx}/{len(result.records)} records")

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
        print("✅ Code Search Acquisition Completed")
        print("="*60)
        print(f"发现: {result.total_found}")
        print(f"保存到数据库: {saved_count}")
        print(f"跳过: {result.total_skipped}")
        print(f"失败: {result.total_failed}")
        print("="*60)

        # Print sample records
        if result.records:
            print("\n示例记录:")
            for i, record in enumerate(result.records[:5], 1):
                if record.get('not_modified'):
                    continue
                print(f"\n{i}. {record['name']}")
                print(f"   仓库: {record['repo_full_name']}")
                print(f"   路径: {record['skill_path']}")
                print(f"   Stars: {record['stars']}")
                print(f"   风险: {record['risk_level']}")

        logger.info(f"Acquisition completed: {result}")

    except Exception as e:
        logger.error(f"Code Search acquisition failed: {e}", exc_info=True)

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
    run_code_search()
