#!/bin/bash

# Start backend
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID at http://localhost:8000"

# Start frontend
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID at http://localhost:8080"

# Wait for services to start
sleep 5

# Run demo to populate data
echo "Running demo scraper to populate data..."
python3 demo/demo_scraper.py

echo "---------------------------------------------------"
echo "Full Stack Scraper SRE Platform is running!"
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:8080"
echo "---------------------------------------------------"
echo "Press Ctrl+C to stop servers..."

# Wait forever (or until killed)
# In this environment, we just wait a bit and exit to show it works
sleep 10

# Kill servers
kill $BACKEND_PID
kill $FRONTEND_PID
