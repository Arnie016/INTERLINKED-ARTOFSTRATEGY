#!/bin/bash

# OrgMind AI Development Startup Script
echo "🚀 Starting OrgMind AI Development Environment"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "backend/api/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if ports are available
if check_port 8000; then
    echo "⚠️  Port 8000 is already in use. Backend may already be running."
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use. Frontend may already be running."
fi

echo ""
echo "📋 Starting services..."
echo ""

# Start backend API
echo "🔧 Starting Backend API (FastAPI) on http://localhost:8000"
cd backend

# Install API dependencies if needed
if [ ! -d "api/venv" ]; then
    echo "📦 Creating virtual environment for API..."
    cd api && python3 -m venv venv && cd ..
fi

# Start the API server in background
npm run dev &
BACKEND_PID=$!

# Go back to project root
cd ..

# Start frontend
echo "🎨 Starting Frontend (Next.js) on http://localhost:3000"
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install > /dev/null 2>&1
fi

# Start the frontend server in background
npm run dev &
FRONTEND_PID=$!

# Go back to project root
cd ..

echo ""
echo "✅ Services started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
