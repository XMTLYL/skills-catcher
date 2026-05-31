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

    try:
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

        # Print summary
        print("\n" + "="*60)
        print("✅ User Submission Processing Completed")
        print("="*60)
        print(f"发现: {result.total_found}")
        print(f"保存: {result.total_saved}")
        print(f"跳过: {result.total_skipped}")
        print(f"失败: {result.total_failed}")
        print("="*60)

        # Print records
        if result.records:
            print("\n处理结果:")
            for i, record in enumerate(result.records, 1):
                print(f"\n{i}. {record['name']}")
                print(f"   仓库: {record['repo_full_name']}")
                print(f"   路径: {record['skill_path']}")
                print(f"   Stars: {record['stars']}")
                print(f"   风险: {record['risk_level']}")

        logger.info(f"Processing completed: {result}")

        # TODO: Save records to database (Phase 5)
        logger.info("Note: Database saving will be implemented in Phase 5")

    except Exception as e:
        logger.error(f"User submission processing failed: {e}", exc_info=True)
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
