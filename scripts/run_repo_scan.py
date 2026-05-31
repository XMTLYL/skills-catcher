"""
Repository scanner acquisition script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.github.client import GitHubClient
from src.parser.skill_parser import SkillParser
from src.scanner.risk_scanner import RiskScanner
from src.scanner.directory_detector import DirectoryDetector
from src.acquisition.repo_scanner import RepoScannerAcquirer
from src.storage.skill_repository import SkillRepository
from src.storage.task_repository import TaskRepository
from src.storage.known_repo_repository import KnownRepositoryRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'repo_scan.log')


def run_repo_scan(repo_full_name=None):
    """
    Run repository scan acquisition

    Args:
        repo_full_name: Optional specific repository to scan
    """
    logger.info("="*60)
    logger.info("Starting Repository Scan Acquisition")
    logger.info("="*60)

    task_id = None

    try:
        # Determine repositories to scan
        if repo_full_name:
            repositories = [repo_full_name]
            logger.info(f"Scanning specific repository: {repo_full_name}")
        else:
            # Load from database
            with KnownRepositoryRepository() as known_repo:
                known_repos = known_repo.find_all_enabled()
                repositories = [r.repo_full_name for r in known_repos]

            if not repositories:
                logger.warning("No known repositories found in database, using defaults")
                repositories = [
                    "anthropics/anthropic-quickstarts",
                    "modelcontextprotocol/servers"
                ]

            logger.info(f"Scanning {len(repositories)} known repositories")

        # Create task record
        with TaskRepository() as task_repo:
            task = task_repo.create_task(
                task_type='repo_tree',
                query_text=', '.join(repositories)
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
        acquirer = RepoScannerAcquirer(
            github_client=github_client,
            parser=parser,
            scanner=scanner,
            detector=detector,
            repositories=repositories
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
                    if record.get('not_modified'):
                        continue

                    skill_repo.upsert(record)
                    saved_count += 1

                    if idx % 10 == 0:
                        logger.info(f"Saved {idx}/{len(result.records)} records")

                except Exception as e:
                    logger.error(f"Failed to save record: {e}")

        logger.info(f"Successfully saved {saved_count} records to database")

        # Update last_scanned for repositories
        with KnownRepositoryRepository() as known_repo:
            for repo in repositories:
                known_repo.update_last_scanned(repo)

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
        print("✅ Repository Scan Completed")
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
        logger.error(f"Repository scan failed: {e}", exc_info=True)

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
    # Check for command line argument
    repo = sys.argv[1] if len(sys.argv) > 1 else None
    run_repo_scan(repo)
