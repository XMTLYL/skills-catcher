#!/bin/bash

# Quick Start Script for GitHub Skill Indexer
# This script helps you quickly set up and run the project

set -e  # Exit on error

echo "============================================================"
echo "GitHub Skill Indexer - Quick Start"
echo "============================================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.11+ is required (found: $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "============================================================"
    echo "⚠️  IMPORTANT: Please edit .env file and fill in:"
    echo "   - GITHUB_TOKEN (required)"
    echo "   - DATABASE_URL (required)"
    echo "============================================================"
    echo ""
    read -p "Press Enter after you've edited .env file..."
else
    echo "✅ .env file exists"
fi
echo ""

# Check if database is configured
echo "Checking database connection..."
if python3 -c "from src.database import engine; engine.connect()" 2>/dev/null; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo ""
    echo "Please check your DATABASE_URL in .env file"
    echo "Example: mysql+pymysql://user:password@localhost:3306/skill_index?charset=utf8mb4"
    exit 1
fi
echo ""

# Initialize database
echo "Initializing database..."
if python3 scripts/init_db.py; then
    echo "✅ Database initialized"
else
    echo "❌ Database initialization failed"
    exit 1
fi
echo ""

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "✅ Logs directory created"
fi

echo "============================================================"
echo "✅ Setup completed successfully!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run Code Search:"
echo "   python main.py code_search"
echo ""
echo "2. Scan a specific repository:"
echo "   python main.py repo_scan --repo anthropics/anthropic-quickstarts"
echo ""
echo "3. View statistics:"
echo "   python main.py stats"
echo ""
echo "4. Get help:"
echo "   python main.py --help"
echo ""
echo "For detailed documentation, see:"
echo "  - README.md"
echo "  - docs/deployment.md"
echo "  - docs/PROJECT_SUMMARY.md"
echo ""
echo "============================================================"
