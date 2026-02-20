#!/bin/bash
# Clean up previous DB
rm -f scraper_sre.db

uvicorn backend.app.main:app --reload --port 8000 &
SERVER_PID=$!
echo "Server started with PID $SERVER_PID"

# Wait for server to start
sleep 5

python3 demo/demo_scraper.py

# Give the server a moment to process background tasks and flush logs
sleep 5

# Kill server
kill $SERVER_PID
