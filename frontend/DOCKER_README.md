# Docker Setup for DAG Generator Frontend

This document explains how to run the frontend using Docker.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### Production Build

To run the full stack (frontend + backend) in production mode:

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5002

### Development Mode

For development with hot reload:

```bash
# Build and start development services
docker-compose -f docker-compose.dev.yml up --build

# Run in detached mode
docker-compose -f docker-compose.dev.yml up -d --build
```

The application will be available at:
- Frontend: http://localhost:5173 (with hot reload)
- Backend API: http://localhost:5002

## Docker Commands

### Building Images

```bash
# Build frontend production image
docker build -t dag-generator-frontend ./frontend

# Build frontend development image
docker build -f ./frontend/Dockerfile.dev -t dag-generator-frontend-dev ./frontend
```

### Running Individual Services

```bash
# Run frontend only (production)
docker run -p 3000:80 dag-generator-frontend

# Run frontend only (development)
docker run -p 5173:5173 -v $(pwd)/frontend:/app -v /app/node_modules dag-generator-frontend-dev
```

### Useful Docker Commands

```bash
# View running containers
docker ps

# View logs
docker logs dag-generator-frontend
docker logs dag-generator-frontend-dev

# Stop all services
docker-compose down

# Stop development services
docker-compose -f docker-compose.dev.yml down

# Remove all containers and images
docker-compose down --rmi all

# Rebuild without cache
docker-compose build --no-cache
```

## Configuration

### Environment Variables

The frontend Docker containers support the following environment variables:

- `VITE_API_URL`: Backend API URL (default: http://localhost:5002)

### Nginx Configuration

The production build uses Nginx with:
- Gzip compression
- Client-side routing support
- Static asset caching
- Security headers

## Troubleshooting

### Port Conflicts

If ports 3000 or 5173 are already in use, modify the port mappings in docker-compose.yml:

```yaml
ports:
  - "8080:80"  # Change 3000 to 8080 for production
  - "8173:5173"  # Change 5173 to 8173 for development
```

### Volume Mounting Issues

On Windows/macOS, ensure Docker has permission to access the project directory.

### Build Failures

Clear Docker cache and rebuild:

```bash
docker system prune -f
docker-compose build --no-cache
```
