#!/bin/bash
# UAE PPP Portal — One-command setup
# Run: bash scripts/setup.sh

set -e
echo "=== UAE PPP Portal Setup ==="

# 1. Create conda environment
echo "[1/6] Creating conda environment 'uae-ppp'..."
conda env create -f conda_env.yml --force
echo "✓ Conda environment created"

# 2. Activate and install Playwright browsers
echo "[2/6] Installing Playwright browsers..."
conda run -n uae-ppp playwright install chromium
echo "✓ Playwright ready"

# 3. Copy .env
echo "[3/6] Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env created — EDIT THIS FILE and add your ANTHROPIC_API_KEY"
else
    echo "✓ .env already exists, skipping"
fi

# 4. Create logs directory
mkdir -p logs
echo "✓ Logs directory ready"

# 5. Initialise database and seed with known projects
echo "[4/6] Initialising database..."
conda run -n uae-ppp python scripts/seed_db.py
echo "✓ Database seeded with 42 projects"

# 6. Install frontend dependencies
echo "[5/6] Installing frontend dependencies..."
cd frontend && npm install && cd ..
echo "✓ Frontend dependencies installed"

# 7. Run tests
echo "[6/6] Running tests..."
conda run -n uae-ppp pytest tests/ -v --tb=short

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Run: bash scripts/run_dev.sh"
echo "  3. Open: http://localhost:5173"
