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
- `table_depends_on` (optional): Array of table-level dependencies in format `["group.table"]`
- `columns` (optional): Array of column definitions
  - `name`: Column name
  - `description` (optional): Column description  
  - `key_type` (optional): `"primary"` or `"foreign"`
  - `depends_on`: Array of column dependencies in format `["group.table.column"]`

### Table-Level Dependencies

You can declare that a table depends on another table using the `table_depends_on` field. This creates a dependency relationship where the table depends on **all columns** of the referenced table:

```yaml
group: stg
table: enriched_orders
description: "Orders enriched with customer data"
table_depends_on: ["src.customers"]  # This table depends on all columns in src.customers
columns:
  - name: order_id
    depends_on: ["src.orders.order_id"]
  - name: customer_name
    depends_on: []  # This gets customer data through table-level dependency
```

You can also create tables with **only** table-level dependencies and no explicit columns:

```yaml
group: mart
table: aggregated_data
description: "Aggregated data from multiple sources"
table_depends_on: 
  - stg.orders
  - stg.customers
  - stg.products
# No explicit columns needed - depends on entire tables
```

**How it works:**
- Table-level dependencies create invisible columns that represent the dependency
- These invisible columns connect to all columns in the referenced table
- The dependencies appear in the DAG lineage visualization
- Invisible columns are never displayed in the frontend but enable table-level lineage tracking

**When to use table-level dependencies:**
- When a table uses data from an entire other table without specific column mapping
- For lookup tables or reference data relationships
- For aggregation or summary tables that use entire source tables
- When you want to show table-level lineage without mapping every individual column

```