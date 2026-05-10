#!/bin/bash
# Setup script for Linux/macOS

set -e

echo "🚀 OpenWebUI Proxy Server Setup"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "✓ Logs directory created"
else
    echo "✓ Logs directory already exists"
fi

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env file created from .env.example"
    echo "⚠️  Please edit .env with your configuration"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env with your OpenWebUI URL"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the server: python -m app.main"
echo ""
