#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing Python dependencies ==="
pip install fastapi uvicorn pydantic

echo "=== Installing frontend dependencies ==="
cd frontend
npm ci --legacy-peer-deps

echo "=== Building React frontend ==="
npm run build
cd ..

echo "=== Build complete ==="
