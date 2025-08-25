# Backend README

## DAG Generator Backend API

This is the backend API service for the DAG Generator project. It provides REST endpoints for analyzing data lineage and dependencies from YAML configuration files.

### Project Structure

```
backend/
├── api/            # REST API endpoints
├── dag/            # DAG assembly and processing logic
├── objects/        # Data model classes (Table, Column, Group)
├── schema/         # JSON schema definitions
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Configuration

The backend can be configured to analyze different project folders:

#### Method 1: Edit the code
In `api/dag_api.py`, change the `TARGET_PROJECT` variable:
```python
TARGET_PROJECT = "your-project-name"  # Change this line
```

#### Method 2: Environment variable
Set the `DAG_TARGET_PROJECT` environment variable:
```bash
export DAG_TARGET_PROJECT=your-project-name
```

Or in docker-compose.yml:
```yaml
environment:
  - DAG_TARGET_PROJECT=your-project-name
```

#### Available Projects
- `finance` (default) - Sample finance domain project
- Add your own project folders under `Projects/`

### Features

#### Table-Level Dependencies
The backend supports table-level dependencies through the `table_depends_on` field in YAML files. This creates invisible columns that represent dependencies on all columns of the referenced table, enabling table-level lineage tracking without explicit column mapping.

#### Column-Level Dependencies
Standard column-to-column dependencies are tracked through the `depends_on` field in column definitions.

### API Endpoints

- `GET /health` - Health check
- `GET /dag` - Complete DAG structure
- `GET /table/<name>/lineage` - Table lineage (supports both 'table' and 'group.table')
- `GET /tables` - List all tables
- `GET /groups` - List all groups
- `GET /stats` - DAG statistics

### Running the Backend

#### With Docker Compose (Recommended)

```bash
cd backend
sudo docker compose up --build
```

The API will be available at `http://localhost:5000`

#### Local Development

```bash
cd backend
pip install -r requirements.txt
python api/dag_api.py
```

### Testing the API

```bash
# Health check
curl http://localhost:5000/health

# Get complete DAG
curl http://localhost:5000/dag

# Get table lineage
curl "http://localhost:5000/table/mart.order/lineage"

# List all tables
curl http://localhost:5000/tables
```
