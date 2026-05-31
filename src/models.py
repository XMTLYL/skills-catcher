"""
SQLAlchemy database models
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, DateTime,
    SmallInteger, JSON, Index, UniqueConstraint
)
from src.database import Base


class GitHubSkill(Base):
    """GitHub Skills index table"""
    __tablename__ = 'github_skills'

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='Primary key')

    # Skill metadata
    name = Column(String(255), nullable=True, comment='Skill name')
    description = Column(Text, nullable=True, comment='Skill description')
    slug = Column(String(255), nullable=True, comment='URL slug')

    # Repository information
    repo_full_name = Column(String(255), nullable=False, comment='Repository full name (owner/repo)')
    repo_owner = Column(String(255), nullable=True, comment='Repository owner')
    repo_name = Column(String(255), nullable=True, comment='Repository name')
    repo_url = Column(String(500), nullable=False, comment='Repository URL')
    repo_default_branch = Column(String(100), nullable=True, comment='Default branch')

    # Skill file information
    skill_path = Column(String(500), nullable=False, comment='SKILL.md path')
    skill_dir = Column(String(500), nullable=True, comment='Skill directory')
    skill_html_url = Column(String(500), nullable=True, comment='GitHub page URL')
    skill_raw_url = Column(String(500), nullable=True, comment='Raw file URL')
    skill_api_url = Column(String(500), nullable=True, comment='GitHub Contents API URL')

    # File metadata
    skill_sha = Column(String(100), nullable=True, comment='File SHA')
    skill_size = Column(Integer, nullable=True, comment='File size')
    skill_etag = Column(String(255), nullable=True, comment='ETag for incremental updates')
    skill_last_modified = Column(String(255), nullable=True, comment='Last-Modified header')

    # Parsed frontmatter
    frontmatter_json = Column(JSON, nullable=True, comment='SKILL.md frontmatter raw data')
    license = Column(String(100), nullable=True, comment='Skill declared license')
    compatibility = Column(String(255), nullable=True, comment='Compatible platforms')
    allowed_tools = Column(Text, nullable=True, comment='Allowed tools')

    # Repository statistics
    stars = Column(Integer, default=0, comment='Repository stars')
    forks = Column(Integer, default=0, comment='Repository forks')
    watchers = Column(Integer, default=0, comment='Repository watchers')
    open_issues = Column(Integer, default=0, comment='Open issues')
    repo_license = Column(String(100), nullable=True, comment='Repository license')
    repo_archived = Column(SmallInteger, default=0, comment='Repository archived')
    repo_disabled = Column(SmallInteger, default=0, comment='Repository disabled')
    repo_private = Column(SmallInteger, default=0, comment='Repository private')
    repo_updated_at = Column(DateTime, nullable=True, comment='Repository updated time')
    repo_pushed_at = Column(DateTime, nullable=True, comment='Repository last push time')

    # Directory structure
    has_scripts = Column(SmallInteger, default=0, comment='Has scripts directory')
    has_assets = Column(SmallInteger, default=0, comment='Has assets directory')
    has_references = Column(SmallInteger, default=0, comment='Has references directory')
    has_tests = Column(SmallInteger, default=0, comment='Has tests directory')

    # Risk assessment
    risk_level = Column(String(50), default='unknown', comment='Risk level: low/medium/high/unknown')
    risk_flags = Column(JSON, nullable=True, comment='Risk flags')
    license_status = Column(String(50), default='unknown', comment='License status: clear/missing/conflict/unknown')

    # Source and status
    source_type = Column(String(50), default='github_search', comment='Source: github_search/trusted_repo/user_submit')
    status = Column(String(50), default='pending', comment='Status: found/parsed/pending/approved/rejected/risky/offline')

    # Timestamps
    first_found_at = Column(DateTime, default=datetime.utcnow, comment='First found time')
    last_checked_at = Column(DateTime, nullable=True, comment='Last checked time')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('repo_full_name', 'skill_path', name='uk_repo_skill_path'),
        Index('idx_name', 'name'),
        Index('idx_repo_full_name', 'repo_full_name'),
        Index('idx_status', 'status'),
        Index('idx_source_type', 'source_type'),
        Index('idx_stars', 'stars'),
        Index('idx_repo_updated_at', 'repo_updated_at'),
        {'comment': 'GitHub Skills index table'}
    )


class GitHubScanTask(Base):
    """GitHub scan tasks table"""
    __tablename__ = 'github_scan_tasks'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    task_type = Column(String(50), nullable=False, comment='Task type: code_search/repo_tree/user_submit/update_check')
    query_text = Column(String(500), nullable=True, comment='Search query or repository address')

    status = Column(String(50), default='pending', comment='Status: pending/running/success/failed')
    total_found = Column(Integer, default=0, comment='Total found')
    total_saved = Column(Integer, default=0, comment='Total saved')
    total_skipped = Column(Integer, default=0, comment='Total skipped')
    error_message = Column(Text, nullable=True, comment='Error message')

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {'comment': 'GitHub scan tasks table'}
    )


class GitHubKnownRepository(Base):
    """Known Skill repositories table"""
    __tablename__ = 'github_known_repositories'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    repo_full_name = Column(String(255), nullable=False, comment='Repository full name (owner/repo)')
    repo_url = Column(String(500), nullable=False, comment='GitHub repository URL')
    source_level = Column(String(50), default='normal', comment='Source level: official/trusted/normal/user')
    scan_enabled = Column(SmallInteger, default=1, comment='Scan enabled')

    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('repo_full_name', name='uk_repo_full_name'),
        {'comment': 'Known Skill repositories table'}
    )
