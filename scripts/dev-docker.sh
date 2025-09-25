#!/bin/bash

# Development with Docker script for Envoyou SEC API

set -e

echo "🐳 Starting Envoyou SEC API Development Environment"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker-compose -f docker-compose.dev.yml up --build -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec envoyou-postgres pg_isready -U envoyou -d envoyou; do
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
docker exec envoyou-api alembic upgrade head

echo "🎉 Development environment is ready!"
echo ""
echo "📋 Services:"
echo "  - API: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "🔧 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.dev.yml down"
echo "  - Restart API: docker-compose -f docker-compose.dev.yml restart envoyou-api"
echo "  - Database shell: docker exec -it envoyou-postgres psql -U envoyou -d envoyou"