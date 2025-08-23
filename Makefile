# DAG Generator Docker Makefile
# Provides convenient commands for Docker operations

.PHONY: help build up down restart logs shell clean validate test health

# Default target
help:
	@echo "DAG Generator Docker Commands:"
	@echo ""
	@echo "  make build      - Build the Docker image"
	@echo "  make up         - Start the services"
	@echo "  make down       - Stop the services"
	@echo "  make restart    - Restart the services"
	@echo "  make logs       - View service logs"
	@echo "  make shell      - Access container shell"
	@echo "  make clean      - Clean up Docker resources"
	@echo "  make validate   - Validate Docker setup"
	@echo "  make test       - Test the API endpoints"
	@echo "  make health     - Check API health"
	@echo ""

# Build the Docker image
build:
	@echo "🐳 Building DAG Generator Docker image..."
	docker build -t dag-generator-api .

# Start services
up:
	@echo "🚀 Starting DAG Generator API..."
	docker-compose up -d

# Stop services
down:
	@echo "🛑 Stopping DAG Generator API..."
	docker-compose down

# Restart services
restart: down build up
	@echo "🔄 Services restarted"

# View logs
logs:
	@echo "📋 Viewing service logs..."
	docker-compose logs -f dag-api

# Access container shell
shell:
	@echo "🐚 Accessing container shell..."
	docker-compose exec dag-api bash

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	@echo "Cleanup complete"

# Validate Docker setup
validate:
	@echo "🔍 Validating Docker setup..."
	@./validate-docker.sh

# Test API endpoints
test:
	@echo "🧪 Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:5000/health || echo "❌ API not responding"
	@echo ""
	@echo "DAG endpoint:"
	@curl -s http://localhost:5000/dag | head -20 || echo "❌ DAG endpoint failed"
	@echo ""
	@echo "Tables endpoint:"
	@curl -s http://localhost:5000/tables | head -10 || echo "❌ Tables endpoint failed"

# Check API health
health:
	@echo "🏥 Checking API health..."
	@curl -s http://localhost:5000/health | python3 -m json.tool || echo "❌ API not healthy"

# Full setup: validate, build, and start
setup: validate build up
	@echo "⏳ Waiting for API to be ready..."
	@sleep 5
	@make health
	@echo "✅ DAG Generator API is ready!"
	@echo "🌐 Available at: http://localhost:5000"
