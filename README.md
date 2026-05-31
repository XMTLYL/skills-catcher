# GitHub Skill Catcher

English | [简体中文](README.zh-CN.md)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/XMTLYL/skills-catcher/workflows/Tests/badge.svg)](https://github.com/XMTLYL/skills-catcher/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A metadata indexing service for automatically discovering, fetching, parsing, and indexing public Skills from GitHub.

## Overview

GitHub skills-catcher is not a crawler or mirror system, but a metadata indexing service that only stores Skill names, descriptions, repository links, Stars, and other information without downloading complete scripts or assets.

### Core Features

- 🔍 **Auto Discovery**: Search for SKILL.md files via GitHub Code Search API
- 📊 **Metadata Extraction**: Parse SKILL.md frontmatter and repository information
- 🛡️ **Risk Scanning**: Detect dangerous commands, API keys, and sensitive information
- 🔄 **Incremental Updates**: Use ETag mechanism to avoid duplicate requests
- 📈 **Statistical Analysis**: Stars, Forks, License, update time, etc.

### Three Acquisition Methods

1. **GitHub Code Search**: Search for SKILL.md in public repositories across GitHub
2. **Repository Scanning**: Scan known high-quality Skill repositories
3. **User Submission**: Users actively submit GitHub repository URLs

## Quick Start

### Requirements

- Python 3.11+
- MySQL 8.0+
- GitHub Personal Access Token

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/XMTLYL/skills-catcher.git
cd skill-catcher
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
nano .env  # Fill in GITHUB_TOKEN and DATABASE_URL
```

4. **Initialize database**
```bash
python scripts/init_db.py
```

5. **Run acquisition tasks**
```bash
# Using unified entry point
python main.py code_search          # Code Search acquisition
python main.py repo_scan            # Repository scanning
python main.py update_check         # Incremental update check
python main.py stats                # Display statistics

# Or use standalone scripts
python scripts/run_code_search.py
python scripts/run_repo_scan.py
python scripts/update_check.py
```

### Complete Deployment Guide

For detailed deployment steps, please refer to: [Deployment Guide](docs/deployment.md)

## Project Structure

```
skill-catcher/
├── config.py                     # Configuration management
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
│
├── src/                          # Source code
│   ├── models.py                 # Database models
│   ├── database.py               # Database connection
│   ├── github/                   # GitHub API interaction layer
│   ├── parser/                   # Parsing layer
│   ├── scanner/                  # Scanning layer
│   ├── acquisition/              # Acquisition strategy layer
│   ├── storage/                  # Storage layer
│   └── utils/                    # Utility layer
│
├── scripts/                      # Standalone scripts
│   ├── init_db.py                # Database initialization
│   ├── run_code_search.py        # Code Search acquisition
│   ├── run_repo_scan.py          # Repository scanning
│   └── update_check.py           # Incremental updates
│
├── tests/                        # Tests
└── logs/                         # Logs
```

## Configuration

### Environment Variables (.env)

```env
# GitHub API Token (required)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Database connection (required)
DATABASE_URL=mysql+pymysql://user:password@host:port/database?charset=utf8mb4

# Log level (optional)
LOG_LEVEL=INFO
```

### Getting GitHub Token

1. Visit https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Check `public_repo` permission
4. Generate and copy the token

## Database Schema

### github_skills (Core Table)

Stores Skill metadata and index information.

**Main Fields:**
- `name`, `description` - Skill name and description
- `repo_full_name`, `repo_url` - Repository information
- `skill_path`, `skill_html_url` - SKILL.md path and link
- `stars`, `forks`, `license` - Repository statistics
- `risk_level`, `risk_flags` - Risk assessment
- `status` - Status (pending/approved/rejected/risky/offline)

### github_scan_tasks (Task Table)

Records the execution status of each acquisition task.

### github_known_repositories (Known Repository Table)

Stores a list of known high-quality Skill repositories.

## Usage Examples

### Manual Code Search

```bash
python scripts/run_code_search.py
```

Example output:
```
[1/30] Processing: openai/skills/pdf-processing/SKILL.md
[2/30] Processing: anthropics/skills/browser/SKILL.md
...
✅ Task completed - Found: 30, Saved: 25, Skipped: 5, Failed: 0
```

### Scheduled Tasks

Using cron for scheduled execution:

```bash
# Edit crontab
crontab -e

# Run Code Search daily at 3 AM
0 3 * * * cd /path/to/skill-catcher && python3 scripts/run_code_search.py >> logs/code_search.log 2>&1

# Scan repositories daily at 4 AM
0 4 * * * cd /path/to/skill-catcher && python3 scripts/run_repo_scan.py >> logs/repo_scan.log 2>&1

# Incremental update every Sunday at 2 AM
0 2 * * 0 cd /path/to/skill-catcher && python3 scripts/update_check.py >> logs/update_check.log 2>&1
```

## Development Guide

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src tests/

# Run specific test file
pytest tests/test_parser.py
```

### Adding New Search Keywords

Edit `config.py`:

```python
SEARCH_QUERIES = [
    'filename:SKILL.md "description:"',
    'filename:SKILL.md "your-new-keyword"',
    # Add more keywords...
]
```

### Adding Known Repositories

```sql
INSERT INTO github_known_repositories
(repo_full_name, repo_url, source_level, scan_enabled)
VALUES
('owner/repo', 'https://github.com/owner/repo', 'trusted', 1);
```

## Risk Scanning Rules

### Risk Levels

- **Low Risk**: Only SKILL.md, no scripts, no dangerous keywords
- **Medium Risk**: Contains scripts, requires API keys, requires network access
- **High Risk**: Contains `rm -rf`, `curl | bash`, `eval()`, `PRIVATE_KEY`

### Keyword List

**High-risk keywords:**
- `rm -rf`, `curl | bash`, `wget`, `eval(`, `exec(`
- `PRIVATE_KEY`, `id_rsa`, `ssh`

**Medium-risk keywords:**
- `subprocess`, `os.system`, `API_KEY`, `SECRET`, `TOKEN`
- `.env`, `process.env`

## Rate Limiting Strategy

- **Code Search API**: 6 requests/minute, 10 seconds interval
- **Contents API**: 0.5-1 second interval
- **Auto Wait**: Proactively wait when `x-ratelimit-remaining` < 10
- **Error Handling**: 403/429 triggers 60-second wait + exponential backoff

## Incremental Update Mechanism

Using ETag and Last-Modified for incremental updates:

1. Save ETag and Last-Modified on first request
2. Include `If-None-Match` and `If-Modified-Since` in subsequent requests
3. On 304 response, only update `last_checked_at` without re-parsing

## Troubleshooting

### Database Connection Failed

Check if `DATABASE_URL` in `.env` is correct:
```bash
mysql -u user -p -h host -P port database
```

### GitHub API Rate Limit

Check if token is valid:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/rate_limit
```

### View Logs

```bash
# View latest logs
tail -f logs/code_search.log

# Search for errors
grep "ERROR" logs/*.log
```

## Contributing

Issues and Pull Requests are welcome! For details, please refer to [Contributing Guide](CONTRIBUTING.md).

## License

This project is licensed under the [Apache-2.0 License](LICENSE).

## Contact

- Submit Issues: [GitHub Issues](https://github.com/XMTLYL/skills-catcher/issues)
- Discussions: [GitHub Discussions](https://github.com/XMTLYL/skills-catcher/discussions)

## References

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Design Document](docs/github_skills_acquisition_plan.md)
