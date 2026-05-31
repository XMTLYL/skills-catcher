"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import Config

# Create base class for models
Base = declarative_base()

# Create engine
engine = create_engine(
    Config.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """
    Get database session

    Returns:
        SQLAlchemy session
    """
    return SessionLocal()


def init_db():
    """
    Initialize database (create all tables)
    """
    from src.models import GitHubSkill, GitHubScanTask, GitHubKnownRepository
    Base.metadata.create_all(bind=engine)
