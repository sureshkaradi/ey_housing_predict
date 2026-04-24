#!/usr/bin/env bash
set -e

# Start App1 backend
uvicorn app1.main:app --host 0.0.0.0 --port 8080 &
PID_APP1=$!

# Start App2 backend
uvicorn app2.main:app --host 0.0.0.0 --port 8081 &
PID_APP2=$!

# Start Next.js frontend
cd next-portal
npm run start -- --hostname 0.0.0.0 --port 3000 &
PID_FRONTEND=$!

wait -n "$PID_APP1" "$PID_APP2" "$PID_FRONTEND"
EXIT_STATUS=$?

kill "$PID_APP1" "$PID_APP2" "$PID_FRONTEND" 2>/dev/null || true
exit "$EXIT_STATUS"
