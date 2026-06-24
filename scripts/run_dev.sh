#!/bin/bash
# Start both backend and frontend for development
set -e

echo "Starting UAE PPP Portal..."

# Start FastAPI backend
conda run -n uae-ppp uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✓ Backend started (PID $BACKEND_PID) → http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"

# Give backend a moment to start
sleep 2

# Start React frontend
cd frontend && npm run dev &
FRONTEND_PID=$!
echo "✓ Frontend started (PID $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "Press Ctrl+C to stop both servers"

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
