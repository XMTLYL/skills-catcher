#!/bin/bash

# Health Check Script for GitHub Skill Indexer
# Checks system health and reports status

set -e

echo "============================================================"
echo "GitHub Skill Indexer - Health Check"
echo "============================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

# 1. Check Python version
echo "1. Checking Python version..."
if python3 --version | grep -q "Python 3.1[1-9]"; then
    print_status 0 "Python version is compatible"
else
    print_status 1 "Python version is not compatible (requires 3.11+)"
fi
echo ""

# 2. Check virtual environment
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    print_status 0 "Virtual environment exists"
else
    print_status 1 "Virtual environment not found"
fi
echo ""

# 3. Check .env file
echo "3. Checking .env file..."
if [ -f ".env" ]; then
    print_status 0 ".env file exists"

    # Check if GITHUB_TOKEN is set
    if grep -q "GITHUB_TOKEN=ghp_" .env; then
        print_status 0 "GITHUB_TOKEN is configured"
    else
        print_status 1 "GITHUB_TOKEN is not configured"
    fi

    # Check if DATABASE_URL is set
    if grep -q "DATABASE_URL=mysql" .env; then
        print_status 0 "DATABASE_URL is configured"
    else
        print_status 1 "DATABASE_URL is not configured"
    fi
else
    print_status 1 ".env file not found"
fi
echo ""

# 4. Check database connection
echo "4. Checking database connection..."
if python3 -c "from src.database import engine; engine.connect()" 2>/dev/null; then
    print_status 0 "Database connection successful"
else
    print_status 1 "Database connection failed"
fi
echo ""

# 5. Check database tables
echo "5. Checking database tables..."
if python3 -c "from src.models import GitHubSkill; from src.database import engine; GitHubSkill.metadata.tables" 2>/dev/null; then
    print_status 0 "Database tables are accessible"
else
    print_status 1 "Database tables not found (run init_db.py)"
fi
echo ""

# 6. Check GitHub API access
echo "6. Checking GitHub API access..."
if python3 -c "from src.github.client import GitHubClient; client = GitHubClient(); client.get_rate_limit()" 2>/dev/null; then
    print_status 0 "GitHub API is accessible"
else
    print_status 1 "GitHub API access failed (check GITHUB_TOKEN)"
fi
echo ""

# 7. Check logs directory
echo "7. Checking logs directory..."
if [ -d "logs" ]; then
    print_status 0 "Logs directory exists"

    # Check log file sizes
    LARGE_LOGS=$(find logs -name "*.log" -size +100M 2>/dev/null | wc -l)
    if [ $LARGE_LOGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Warning: $LARGE_LOGS log file(s) larger than 100MB${NC}"
    fi
else
    print_status 1 "Logs directory not found"
fi
echo ""

# 8. Check recent task execution
echo "8. Checking recent task execution..."
RECENT_TASKS=$(python3 -c "
from src.storage.task_repository import TaskRepository
with TaskRepository() as repo:
    stats = repo.get_task_stats()
    print(stats.get('total', 0))
" 2>/dev/null)

if [ ! -z "$RECENT_TASKS" ] && [ $RECENT_TASKS -gt 0 ]; then
    print_status 0 "Found $RECENT_TASKS task(s) in database"
else
    echo -e "${YELLOW}⚠️  No tasks found (system not yet used)${NC}"
fi
echo ""

# 9. Check disk space
echo "9. Checking disk space..."
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    print_status 0 "Disk space is sufficient ($DISK_USAGE% used)"
else
    print_status 1 "Disk space is low ($DISK_USAGE% used)"
fi
echo ""

# Summary
echo "============================================================"
echo "Health Check Summary"
echo "============================================================"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! System is healthy.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the errors above.${NC}"
    exit 1
fi
