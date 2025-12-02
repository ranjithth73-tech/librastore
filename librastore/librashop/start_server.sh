#!/bin/bash

# LibraStore Development Server Startup Script
# This script ensures Django is properly set up and starts the development server

echo "========================================="
echo "  LibraStore Development Server"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "✓ Virtual environment found"
    source env/bin/activate
elif [ -d "../venv" ]; then
    echo "✓ Virtual environment found"
    source ../venv/bin/activate
else
    echo "⚠ No virtual environment found"
    echo "  Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "  Installing requirements..."
    pip install -r requirements.txt
fi

echo ""
echo "Checking Django installation..."
python3 -c "import django; print(f'✓ Django {django.get_version()} installed')" 2>/dev/null || {
    echo "✗ Django not installed"
    echo "  Installing requirements..."
    pip install -r requirements.txt
}

echo ""
echo "Running migrations..."
python3 manage.py migrate --noinput

echo ""
echo "Creating logs directory..."
mkdir -p logs

echo ""
echo "Checking for existing server on port 8080..."
# Kill any existing server on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

echo ""
echo "========================================="
echo "  Starting Development Server"
echo "========================================="
echo ""
echo "Server will be available at:"
echo "  → http://localhost:8080/"
echo "  → http://127.0.0.1:8080/"
echo ""
echo "Admin panel:"
echo "  → http://localhost:8080/admin/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="
echo ""

# Start the development server on port 8080
python3 manage.py runserver 8080
