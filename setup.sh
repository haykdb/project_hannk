#!/bin/bash

# Binance EOD Collector - Quick Start Setup Script

set -e

echo "=================================================="
echo "Binance EOD Data Collector - Setup"
echo "=================================================="
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed"
    echo ""
    echo "Please install Poetry first:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    echo ""
    echo "Or visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "✓ Poetry found: $(poetry --version)"
echo ""

# Install dependencies
echo "Installing dependencies..."
poetry install

echo ""
echo "✓ Dependencies installed successfully!"
echo ""

# Test installation
echo "Testing installation..."
poetry run python -c "from binance_eod_collector import BinanceEODCollector; print('✓ Package imported successfully')"

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Quick Start Commands:"
echo ""
echo "1. Collect historical data (test with 10 symbols):"
echo "   poetry run collect-data --max-symbols 10 --days 30"
echo ""
echo "2. Collect historical data (all symbols):"
echo "   poetry run collect-data --days 365"
echo ""
echo "3. Daily update:"
echo "   poetry run update-data"
echo ""
echo "4. Run example ML preprocessing:"
echo "   poetry run python examples/ml_preprocessing_example.py"
echo ""
echo "For more options, see README.md"
echo ""
