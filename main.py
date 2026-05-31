"""
Main entry point for GitHub Skill Indexer
"""
import sys
import argparse
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'main.log')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='GitHub Skill Indexer - Discover and index SKILL.md files from GitHub'
    )

    parser.add_argument(
        'command',
        choices=['code_search', 'repo_scan', 'update_check', 'user_submit'],
        help='Command to execute'
    )

    parser.add_argument(
        '--repo',
        type=str,
        help='Repository full name (for repo_scan and user_submit)'
    )

    parser.add_argument(
        '--path',
        type=str,
        help='Skill path (for user_submit)'
    )

    args = parser.parse_args()

    logger.info(f"Starting command: {args.command}")

    try:
        if args.command == 'code_search':
            from scripts.run_code_search import run_code_search
            run_code_search()

        elif args.command == 'repo_scan':
            from scripts.run_repo_scan import run_repo_scan
            run_repo_scan(args.repo)

        elif args.command == 'update_check':
            from scripts.update_check import run_update_check
            run_update_check()

        elif args.command == 'user_submit':
            if not args.repo:
                logger.error("--repo is required for user_submit command")
                sys.exit(1)
            from scripts.run_user_submit import run_user_submit
            run_user_submit(args.repo, args.path)

        logger.info(f"Command {args.command} completed successfully")

    except Exception as e:
        logger.error(f"Command {args.command} failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
