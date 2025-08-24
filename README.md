# DAG Generator

A data lineage visualization tool that generates interactive DAGs from YAML table definitions.

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Run the Application
```bash
docker compose up --build
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5002

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

```