# DAG Generator - Docker Setup

This document describes how to run the DAG Generator API using Docker.

## 🐳 Docker Setup

The DAG Generator backend has been containerized for easy deployment and development. The setup includes:

- **Dockerfile**: Multi-stage build optimized for Python applications
- **docker-compose.yml**: Service orchestration with volume mounting
- **start-docker.sh**: Automated build and startup script

## 📁 Project Structure for Docker

```
dag_generator/
├── api/                    # API code (included in container)
├── dag/                    # DAG assembly logic (included in container)
├── objects/                # Data models (included in container)
├── schema/                 # JSON schemas (included in container)
├── Projects/               # YAML project files (mounted as volume)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Service orchestration
├── start-docker.sh         # Startup script
└── .dockerignore          # Docker build exclusions
```

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
./start-docker.sh
```

### Option 2: Manual Steps
```bash
# Build the image
docker build -t dag-generator-api .

# Start the service
docker-compose up -d

# Check health
curl http://localhost:5000/health
```

## 📡 API Endpoints

Once running, the API will be available at `http://localhost:5000`:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /dag` | Complete DAG export |
| `GET /table/<name>/lineage` | Single table lineage |
| `GET /tables` | List all tables |
| `GET /groups` | List all groups |
| `GET /stats` | DAG statistics |

## 💾 Data Persistence

- **Projects Folder**: Mounted as read-only volume from `./Projects` to `/app/Projects`
- **Configuration**: All YAML files in the Projects folder are accessible to the containerized API
- **Live Updates**: Changes to YAML files are reflected immediately (restart container to reload)

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV=production` (set in docker-compose.yml)
- `PYTHONPATH=/app` (set in docker-compose.yml)

### Port Mapping
- Container port `5000` → Host port `5000`
- Customizable in `docker-compose.yml`

### Volume Mounts
- `./Projects:/app/Projects:ro` (read-only mount)

## 🛠 Development Workflow

### Making Code Changes
1. Edit source files (api/, dag/, objects/)
2. Rebuild container: `docker-compose down && docker build -t dag-generator-api . && docker-compose up -d`

### Adding New YAML Projects
1. Add YAML files to the `./Projects` folder
2. Files are immediately available to the API (no rebuild needed)

### Updating Dependencies
1. Edit `requirements.txt`
2. Rebuild container: `docker build -t dag-generator-api .`

## 🐛 Troubleshooting

### Check Container Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs dag-api
docker-compose logs -f dag-api  # Follow logs
```

### Shell Access
```bash
docker-compose exec dag-api bash
```

### Stop Services
```bash
docker-compose down
```

### Clean Restart
```bash
docker-compose down
docker system prune -f
docker build -t dag-generator-api .
docker-compose up -d
```

## 🏗 Container Details

### Base Image
- `python:3.11-slim` - Lightweight Python runtime

### Security
- Non-root user execution
- Read-only Projects volume mount
- Health check monitoring

### Performance
- Multi-stage build for smaller image size
- Dependency caching optimization
- System package cleanup

### Monitoring
- Built-in health check endpoint
- Container health monitoring
- Automatic restart on failure

## 📋 Production Considerations

### Scaling
- Single container deployment
- Can be scaled horizontally if needed
- Stateless design (reads from mounted files)

### Security
- Projects folder mounted read-only
- No sensitive data in container
- Standard Flask security practices

### Monitoring
- Health check endpoint available
- Container metrics via Docker
- Application logs via docker-compose

## 🔄 CI/CD Integration

The Docker setup is ready for CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Build and Test
  run: |
    docker build -t dag-generator-api .
    docker run -d -p 5000:5000 -v ./Projects:/app/Projects:ro dag-generator-api
    sleep 10
    curl -f http://localhost:5000/health
```
