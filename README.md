# DAG Generator

A comprehensive data lineage visualization tool with a React frontend and Python Flask backend. This application helps you visualize table and column dependencies in your data pipeline, making it easy to understand data flow and lineage relationships.

## Features

- **Interactive DAG Visualization**: View your data pipeline as an interactive directed acyclic graph
- **Table Details Panel**: Click on any table to see detailed information including:
  - Table descriptions
  - Column names, descriptions, and key types (Primary Key/Foreign Key)
  - Column lineage and dependencies
  - Source column tracking
- **Project Support**: Switch between different data projects
- **Column-Level Lineage**: Track dependencies down to individual columns
- **Key Indicators**: Visual indicators for primary and foreign keys
- **Responsive UI**: Clean, modern interface built with React and TypeScript

## Architecture

- **Frontend**: React + TypeScript + Vite (served via Nginx in production)
- **Backend**: Python Flask API with CORS support
- **Data Format**: YAML files defining table structures and dependencies
- **Containerization**: Docker and Docker Compose for easy deployment

## Project Structure

```
dag_generator/
├── backend/            # Backend API service
│   ├── api/           # REST API endpoints
│   ├── dag/           # DAG assembly logic
│   ├── objects/       # Data model classes
│   ├── schema/        # JSON schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # React frontend application
│   ├── src/
│   │   ├── components/  # React components
│   │   └── assets/      # Static assets
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── projects/          # YAML project files
│   ├── finance/       # Finance domain example
│   └── sample/        # Sample project
├── docker-compose.yml # Full stack orchestration
└── README.md
```

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed on your system
- Git (to clone the repository)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd dag_generator
```

### 2. Start the Application
```bash
docker compose up --build
```

This will:
- Build and start the backend API server on http://localhost:5002
- Build and start the frontend on http://localhost:3000
- Mount the `projects/` directory so you can edit YAML files locally

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5002
- **Health Check**: http://localhost:5002/health

## Development Setup

### Backend Development

#### Prerequisites
- Python 3.11+ 
- pip

#### Setup
```bash
cd backend
pip install -r requirements.txt
python3 api/dag_api.py
```

The backend will be available at http://localhost:5002

### Frontend Development

#### Prerequisites
- Node.js 18+
- npm

#### Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173 (development server)

# View all tables
curl http://localhost:5000/tables
```

## Development

See individual service READMEs for detailed development instructions:
- [Backend README](backend/README.md)

## Future Frontend

A frontend service will be added later with its own Docker setup that connects to this backend API.

## Backend API Endpoints

- `GET /health` - Health check
- `GET /project` - Get current project info
- `POST /project/<name>` - Switch to different project
- `GET /dag` - Complete DAG structure
- `GET /table/<name>/lineage` - Table lineage details
- `GET /tables` - List all tables
- `GET /groups` - List all groups
- `GET /stats` - DAG statistics

## Project Configuration

### YAML File Structure

Create YAML files in the `projects/<project-name>/` directory. Each file represents a table:

```yaml
group: src
table: orders
description: "Source table containing raw order data from the e-commerce platform"
columns:
  - name: order_id
    description: "Unique identifier for each order"
    key_type: "primary"
    depends_on: []
  - name: user_id
    description: "Foreign key reference to the customer"
    key_type: "foreign"
    depends_on: []
  - name: order_date
    description: "Date and time when the order was placed"
    depends_on: []
```

#### YAML Schema
- `group`: Logical grouping (e.g., `src`, `stg`, `mart`)
- `table`: Table name
- `description` (optional): Table description
- `columns`: Array of column definitions
  - `name`: Column name
  - `description` (optional): Column description  
  - `key_type` (optional): `"primary"` or `"foreign"`
  - `depends_on`: Array of column dependencies in format `["group.table.column"]`

### Example Project Structure
```
projects/
  finance/
    src_orders.yml
    src_customers.yml
    src_order_items.yml
    stg_enriched_orders.yml
    mart_order.yml
  sample/
    raw_users.yml
    processed_active_users.yml
```

## Docker Configuration

### Production Deployment
```bash
docker compose up -d
```

### Development with Hot Reload
```bash
docker compose -f docker-compose.dev.yml up
```

### Environment Variables
- `DAG_TARGET_PROJECT`: Set the default project (defaults to first available)
- `FLASK_ENV`: Set to `development` for debug mode

## Usage

1. **Start the Application**: Use Docker Compose or run backend/frontend separately
2. **Load Your Data**: Place YAML files in `projects/<project-name>/`
3. **View the DAG**: Open the frontend and see your data pipeline visualization
4. **Explore Lineage**: Click on tables to see detailed column lineage information
5. **Switch Projects**: Use the API or frontend controls to switch between projects

## Example API Usage

```bash
# Health check
curl http://localhost:5002/health

# Get complete DAG structure
curl http://localhost:5002/dag

# Get lineage for a specific table
curl "http://localhost:5002/table/src.orders/lineage"

# List all tables
curl http://localhost:5002/tables

# Get project statistics
curl http://localhost:5002/stats
```

## Troubleshooting

### Common Issues

**Backend fails to start:**
- Ensure port 5002 is not in use
- Check that `projects/` directory exists and contains valid YAML files
- Verify all Python dependencies are installed

**Frontend build fails:**
- Ensure Node.js 18+ is installed
- Run `npm install` in the frontend directory
- Check for TypeScript errors

**Docker issues:**
- Make sure Docker daemon is running
- Try `docker compose down` then `docker compose up --build`
- Check Docker logs: `docker compose logs backend` or `docker compose logs frontend`

### Logs and Debugging

View container logs:
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs -f  # Follow logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open a GitHub issue or contact the development team.
