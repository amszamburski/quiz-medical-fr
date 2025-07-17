#!/bin/bash
set -e

echo "🚀 Setting up French Medical Quiz MVP..."

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements-dev.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
python -m playwright install chromium

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating project structure..."
mkdir -p app/{templates,static/{css,js},routes,services,models,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p data
mkdir -p scripts

# Copy environment file
echo "🔐 Setting up environment file..."
cp .env.example .env

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'make dev' to start development server"
echo "3. Run 'make test' to run tests"
