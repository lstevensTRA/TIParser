#!/bin/bash

echo "Starting TI Parser Backend and Frontend..."

# Kill any existing processes
echo "Killing existing processes..."
pkill -f "nodemon\|vite\|node.*backend\|node.*frontend" 2>/dev/null || true

# Start backend
echo "Starting backend server on port 3001..."
cd backend
npm run dev &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Test backend
echo "Testing backend..."
curl -s http://localhost:3001/api/health
echo ""

# Start frontend
echo "Starting frontend server on port 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Test frontend
echo "Testing frontend..."
curl -s -I http://localhost:3000 | head -1

echo ""
echo "Servers started!"
echo "Backend: http://localhost:3001"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait 