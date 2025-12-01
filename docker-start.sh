#!/bin/bash

# Docker deployment startup script for Sales Analytics Dashboard

set -e

echo "🚀 Starting Sales Analytics Dashboard with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose."
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "📦 Building and starting containers..."
$COMPOSE_CMD up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Wait for MongoDB
echo "  Waiting for MongoDB..."
until $COMPOSE_CMD exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
    echo "    MongoDB is not ready yet..."
    sleep 2
done
echo "  ✅ MongoDB is ready"

# Wait for Backend
echo "  Waiting for Backend API..."
until curl -f http://localhost:8001/api/ > /dev/null 2>&1; do
    echo "    Backend is not ready yet..."
    sleep 2
done
echo "  ✅ Backend API is ready"

# Wait for Frontend
echo "  Waiting for Frontend..."
sleep 10  # Frontend takes longer to start
echo "  ✅ Frontend should be ready"

echo ""
echo "✅ All services are running!"
echo ""
echo "📍 Access the application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8001"
echo "   API Docs:  http://localhost:8001/docs"
echo ""
echo "🔐 Login:"
echo "   Click 'Demo Access' button on the login page"
echo ""
echo "📊 View logs:"
echo "   $COMPOSE_CMD logs -f"
echo ""
echo "🛑 Stop services:"
echo "   $COMPOSE_CMD down"
echo ""


