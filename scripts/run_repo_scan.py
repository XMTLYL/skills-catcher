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

    try:
        # Initialize components
        logger.info("Initializing components...")
        github_client = GitHubClient()
        parser = SkillParser()
        scanner = RiskScanner()
        detector = DirectoryDetector()

        # Determine repositories to scan
        if repo_full_name:
            repositories = [repo_full_name]
            logger.info(f"Scanning specific repository: {repo_full_name}")
        else:
            # TODO: Load from database in Phase 5
            repositories = [
                "anthropics/anthropic-quickstarts",
                "modelcontextprotocol/servers"
            ]
            logger.info(f"Scanning {len(repositories)} known repositories")

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

        # Print summary
        print("\n" + "="*60)
        print("✅ Repository Scan Completed")
        print("="*60)
        print(f"发现: {result.total_found}")
        print(f"保存: {result.total_saved}")
        print(f"跳过: {result.total_skipped}")
        print(f"失败: {result.total_failed}")
        print("="*60)

        # Print sample records
        if result.records:
            print("\n示例记录:")
            for i, record in enumerate(result.records[:5], 1):
                print(f"\n{i}. {record['name']}")
                print(f"   仓库: {record['repo_full_name']}")
                print(f"   路径: {record['skill_path']}")
                print(f"   Stars: {record['stars']}")
                print(f"   风险: {record['risk_level']}")

        logger.info(f"Acquisition completed: {result}")

        # TODO: Save records to database (Phase 5)
        logger.info("Note: Database saving will be implemented in Phase 5")

    except Exception as e:
        logger.error(f"Repository scan failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check for command line argument
    repo = sys.argv[1] if len(sys.argv) > 1 else None
    run_repo_scan(repo)
