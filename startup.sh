#!/bin/bash

echo "Starting Backend (FastAPI)..."
source venv/bin/activate
# Run backend on port 8000 in the background
uvicorn backend.main:app --port 8000 --reload &
BACKEND_PID=$!

echo "Starting Frontend (Next.js)..."
cd frontend
# Run frontend on port 3000
npm run dev &
FRONTEND_PID=$!

echo "Both systems are starting up!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press CTRL+C to stop both."

# Trap CTRL+C to kill both services
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Wait indefinitely to keep script alive
wait
