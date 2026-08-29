#!/usr/bin/env bash
# ==============================================================================
# VOLTRON Local Stack Startup Script
# Starts FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000)
# ==============================================================================

set -e

# Graceful cleanup on Ctrl+C / EXIT
cleanup() {
    echo ""
    echo "Shutting down VOLTRON services..."
    kill $(jobs -p) 2>/dev/null || true
    echo "Services stopped cleanly."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "============================================================"
echo "⚡ STARTING VOLTRON STRATEGIC AI OPTIONS DECISION SYSTEM"
echo "============================================================"

# 1. Start Backend API
echo "Starting FastAPI Backend on http://localhost:8000 ..."
PYTHONPATH=apps/api python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be healthy
echo "Waiting for Backend health check..."
for i in {1..15}; do
    if curl -s http://localhost:8000/api/health >/dev/null; then
        echo "Backend is HEALTHY at http://localhost:8000"
        break
    fi
    sleep 1
done

# 2. Start Frontend Web
echo "Starting Next.js Frontend on http://localhost:3000 ..."
npm --workspace=apps/web run dev &
FRONTEND_PID=$!

echo "============================================================"
echo "🚀 VOLTRON IS LIVE:"
echo "   - Web App:      http://localhost:3000/terminal"
echo "   - API Docs:     http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/api/health"
echo "============================================================"
echo "Press Ctrl+C to stop all services."

wait
