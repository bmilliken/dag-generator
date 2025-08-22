#!/bin/bash

# Start script for DAG Generator project
set -e

echo "🚀 Starting DAG Generator..."

# Activate virtual environment and start backend server
echo "📡 Starting backend server on http://localhost:8000..."
cd Backend
../.venv/bin/python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start frontend server
echo "⚛️  Starting frontend server on http://localhost:5173..."
cd ../Frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are starting up!"
echo "   📡 Backend API: http://localhost:8000"
echo "   ⚛️  Frontend:    http://localhost:5173"
echo "   📖 API docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT

# Wait for both processes
wait
