#!/bin/bash
# Start Dashy locally with Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Dashy - Local Deployment"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set a strong SECRET_KEY and POSTGRES_PASSWORD!"
    echo ""
    read -p "Press Enter to continue with default values (insecure) or Ctrl+C to edit .env first..."
    echo ""
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🐳 Building and starting services..."
echo ""

# Build and start
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo ""

# Wait for health checks
sleep 5

# Check if backend is healthy
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "  Waiting for backend... ($i/30)"
    sleep 2
done

echo ""
echo "========================================"
echo "  🎉 Dashy is running!"
echo "========================================"
echo ""
echo "  📱 Frontend:  http://localhost:8000"
echo "  📊 Dashboard: http://localhost:8000/dashboard"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "  🗄️  PostgreSQL: localhost:5432"
echo "  ⚡ Redis:      localhost:6379"
echo ""
echo "Commands:"
echo "  ./stop.sh     - Stop all services"
echo "  ./logs.sh     - View logs"
echo "  docker-compose logs -f backend  - View backend logs"
echo ""
echo "========================================"
