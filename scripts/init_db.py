"""
Database initialization script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, engine, get_session
from src.models import GitHubKnownRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'init_db.log')


def main():
    """Initialize database and insert seed data"""
    try:
        logger.info("Starting database initialization...")

        # Create all tables
        init_db()
        logger.info("✅ All tables created successfully")

        # Insert seed data for known repositories
        session = get_session()
        try:
            # Check if seed data already exists
            existing_count = session.query(GitHubKnownRepository).count()

            if existing_count == 0:
                logger.info("Inserting seed data for known repositories...")

                seed_repos = [
                    {
                        'repo_full_name': 'anthropics/anthropic-quickstarts',
                        'repo_url': 'https://github.com/anthropics/anthropic-quickstarts',
                        'source_level': 'official',
                        'scan_enabled': 1
                    },
                    {
                        'repo_full_name': 'modelcontextprotocol/servers',
                        'repo_url': 'https://github.com/modelcontextprotocol/servers',
                        'source_level': 'trusted',
                        'scan_enabled': 1
                    },
                    {
                        'repo_full_name': 'Xquik-dev/x-twitter-scraper',
                        'repo_url': 'https://github.com/Xquik-dev/x-twitter-scraper',
                        'source_level': 'normal',
                        'scan_enabled': 1
                    }
                ]

                for repo_data in seed_repos:
                    repo = GitHubKnownRepository(**repo_data)
                    session.add(repo)

                session.commit()
                logger.info(f"✅ Inserted {len(seed_repos)} seed repositories")
            else:
                logger.info(f"Seed data already exists ({existing_count} repositories)")

        finally:
            session.close()

        logger.info("✅ Database initialization completed successfully")
        print("\n" + "="*60)
        print("Database initialization completed!")
        print("="*60)
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your GITHUB_TOKEN and DATABASE_URL")
        print("3. Run: python scripts/run_code_search.py")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Please check your database connection settings in .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
