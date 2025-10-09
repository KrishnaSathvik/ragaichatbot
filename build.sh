#!/usr/bin/env bash
# Build script for Render deployment

set -e  # Exit on error

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "==> Build completed successfully!"

