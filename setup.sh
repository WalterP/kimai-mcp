#!/bin/bash
# KIMAI MCP Server - Quick Setup Script

set -e

echo "🚀 KIMAI MCP Server Setup"
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "   Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ Found uv package manager"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
else
    echo "✓ Virtual environment already exists"
fi

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your KIMAI_BASE_URL and KIMAI_API_TOKEN"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your KIMAI credentials"
echo "  2. Test connection: source .venv/bin/activate && python3 test_connection.py"
echo "  3. Add to Claude Desktop config (see README.md)"
echo ""
