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
        description='GitHub Skill Indexer - Discover and index SKILL.md files from GitHub',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Code Search acquisition
  python main.py code_search

  # Scan specific repository
  python main.py repo_scan --repo openai/skills

  # Scan all known repositories
  python main.py repo_scan

  # Process user submission
  python main.py user_submit --repo anthropics/anthropic-quickstarts

  # Process user submission with specific path
  python main.py user_submit --repo openai/skills --path skills/pdf/SKILL.md

  # Run incremental update check
  python main.py update_check

  # Show statistics
  python main.py stats
        """
    )

    parser.add_argument(
        'command',
        choices=['code_search', 'repo_scan', 'update_check', 'user_submit', 'stats'],
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

    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Limit for update_check (default: 100)'
    )

    args = parser.parse_args()

    logger.info(f"Starting command: {args.command}")
    print(f"\n{'='*60}")
    print(f"GitHub Skill Indexer - {args.command.upper()}")
    print(f"{'='*60}\n")

    try:
        if args.command == 'code_search':
            from scripts.run_code_search import run_code_search
            run_code_search()

        elif args.command == 'repo_scan':
            from scripts.run_repo_scan import run_repo_scan
            run_repo_scan(args.repo)

        elif args.command == 'update_check':
            from scripts.update_check import run_update_check
            run_update_check(args.limit)

        elif args.command == 'user_submit':
            if not args.repo:
                logger.error("--repo is required for user_submit command")
                print("❌ Error: --repo is required for user_submit command")
                print("\nUsage: python main.py user_submit --repo owner/repo [--path path/to/SKILL.md]")
                sys.exit(1)
            from scripts.run_user_submit import run_user_submit
            run_user_submit(args.repo, args.path)

        elif args.command == 'stats':
            from scripts.show_stats import show_stats
            show_stats()

        logger.info(f"Command {args.command} completed successfully")

    except KeyboardInterrupt:
        logger.warning("Command interrupted by user")
        print("\n\n⚠️  Command interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Command {args.command} failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
