"""
Configuration management for GitHub Skill Indexer
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""

    # GitHub API
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_API_VERSION = "2022-11-28"

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/skill_index?charset=utf8mb4"
    )

    # Rate Limiting
    CODE_SEARCH_RATE_LIMIT = 6  # requests per minute
    CODE_SEARCH_INTERVAL = 10  # seconds between requests
    CONTENTS_API_INTERVAL = 0.5  # seconds between requests
    RATE_LIMIT_THRESHOLD = 10  # remaining requests before waiting

    # Search Configuration
    SEARCH_QUERIES = [
        'filename:SKILL.md "description:"',
        'filename:SKILL.md "name:"',
        'filename:SKILL.md "allowed-tools"',
        'path:skills filename:SKILL.md',
    ]
    MAX_PAGES_PER_QUERY = 2
    RESULTS_PER_PAGE = 30

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = "logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Risk Scanning
    HIGH_RISK_KEYWORDS = [
        "rm -rf",
        "curl | bash",
        "wget",
        "eval(",
        "exec(",
        "PRIVATE_KEY",
        "id_rsa",
        "ssh",
    ]

    MEDIUM_RISK_KEYWORDS = [
        "subprocess",
        "os.system",
        "API_KEY",
        "SECRET",
        "TOKEN",
        ".env",
        "process.env",
    ]

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required in .env file")

        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required in .env file")

        return True


# Validate configuration on import
if __name__ != "__main__":
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please create a .env file based on .env.example")
