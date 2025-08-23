# DAG Generator

A data lineage analysis tool that processes YAML configuration files to build and visualize data dependency graphs.

## Project Structure

```
dag_generator/
├── backend/            # Backend API service
│   ├── api/           # REST API endpoints
│   ├── dag/           # DAG assembly logic
│   ├── objects/       # Data model classes
│   ├── schema/        # JSON schemas
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── Projects/          # Sample YAML projects
│   └── finance/       # Finance domain example
├── docker-compose.yml # Full stack orchestration (for future frontend)
└── README.md
```

## Quick Start

### Backend Only

```bash
cd backend
sudo docker compose up --build
```

The backend API will be available at `http://localhost:5000`

### API Endpoints

- `GET /health` - Health check
- `GET /dag` - Complete DAG structure
- `GET /table/<name>/lineage` - Table lineage with column dependencies
- `GET /tables` - List all tables
- `GET /groups` - List all groups
- `GET /stats` - DAG statistics

### Example Usage

```bash
# Health check
curl http://localhost:5000/health

# Get lineage for a specific table
curl "http://localhost:5000/table/mart.order/lineage"

# View all tables
curl http://localhost:5000/tables
```

## Development

See individual service READMEs for detailed development instructions:
- [Backend README](backend/README.md)

## Future Frontend

A frontend service will be added later with its own Docker setup that connects to this backend API.
