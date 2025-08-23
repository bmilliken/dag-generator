#!/bin/bash

# DAG Generator Docker Startup Script
# Builds and runs the DAG Generator API in Docker

set -e

echo "🐳 Building DAG Generator Docker image..."
docker build -t dag-generator-api .

echo "🚀 Starting DAG Generator API container..."
docker-compose up -d

echo "⏳ Waiting for API to be healthy..."
sleep 5

# Wait for health check
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "✅ DAG Generator API is running!"
        echo ""
        echo "🌐 Available endpoints:"
        echo "  http://localhost:5000/health     - Health check"
        echo "  http://localhost:5000/dag        - Complete DAG export"
        echo "  http://localhost:5000/tables     - List all tables"
        echo "  http://localhost:5000/groups     - List all groups"
        echo "  http://localhost:5000/stats      - DAG statistics"
        echo "  http://localhost:5000/table/<name>/lineage - Table lineage"
        echo ""
        echo "📁 Projects folder is mounted from ./Projects"
        echo "🔄 To rebuild: docker-compose down && docker build -t dag-generator-api . && docker-compose up -d"
        echo "🛑 To stop: docker-compose down"
        exit 0
    fi
    echo "Waiting for API... ($i/30)"
    sleep 2
done

echo "❌ API failed to start within 60 seconds"
echo "Check logs with: docker-compose logs dag-api"
exit 1
