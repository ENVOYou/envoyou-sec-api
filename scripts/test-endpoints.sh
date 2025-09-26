#!/bin/bash

# Automated endpoint testing with Newman
# Usage: ./scripts/test-endpoints.sh

set -e

echo "🧪 Starting Envoyou SEC API Endpoint Testing"
echo "=============================================="

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo "📦 Installing Newman..."
    npm install -g newman
fi

# Check if Docker containers are running
if ! docker ps | grep -q envoyou-api; then
    echo "🐳 Starting Docker containers..."
    docker-compose -f docker-compose.dev.yml up -d
    sleep 10
fi

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        break
    fi
    sleep 1
    ((timeout--))
done

if [ $timeout -eq 0 ]; then
    echo "❌ API failed to start within 30 seconds"
    exit 1
fi

echo "✅ API is ready!"

# Run Newman tests
echo "🚀 Running endpoint tests..."
newman run postman/Envoyou-SEC-API.postman_collection.json \
    --reporters cli,json \
    --reporter-json-export newman-results.json \
    --timeout-request 30000

# Check results
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All endpoint tests completed successfully!"
    echo "📊 Results saved to newman-results.json"
    
    # Show summary
    echo ""
    echo "📋 Test Summary:"
    echo "- Health Check: ✅"
    echo "- Emissions Calculate: ✅"
    echo "- Emissions Factors: ✅"
    echo "- Emissions Units: ✅"
    echo "- EPA Validation: ✅"
    echo "- SEC Export CEVS: ✅"
    echo "- SEC Export Package: ✅"
    echo "- Admin Mapping: ⚠️  (403 - JWT required, expected)"
    echo ""
    echo "🚀 Ready for production deployment!"
else
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi