# DAG JSON API Documentation

A REST API that exposes the DAG lineage data through HTTP endpoints.

## 🚀 Starting the Server

```bash
cd api/
/home/brodiemilli/.pyenv/versions/3.11.9/bin/python dag_api.py
```

The server will start on `http://localhost:5000`

## 📊 Available Endpoints

### 1. Health Check
- **GET** `/health`
- **Description**: Check if the API is running
- **Response**: 
```json
{
  "status": "healthy",
  "message": "DAG JSON API is running"
}
```

### 2. Complete DAG Structure
- **GET** `/dag`
- **Description**: Get the complete DAG with all groups, tables, and connections
- **Response**: Same as `JSONExporter.to_json()`
```json
{
  "groups": [
    {
      "group": "src",
      "tables": ["customers", "orders", "order_items"]
    }
  ],
  "connections": [
    {
      "from": "src.orders",
      "to": "stg.enriched_orders"
    }
  ]
}
```

### 3. Table Lineage
- **GET** `/table/<table_name>/lineage`
- **Description**: Get complete lineage for a specific table including tables, connections, and column details
- **Parameters**: 
  - `table_name`: Table name (supports both `orders` and `src.orders`)
- **Response**: Same as `JSONExporter.table_lineage_json()`
- **Examples**:
  - `/table/enriched_orders/lineage`
  - `/table/stg.enriched_orders/lineage`
  - `/table/order/lineage`

### 4. List All Tables
- **GET** `/tables`
- **Description**: Get a list of all tables with metadata
- **Response**:
```json
{
  "total_tables": 5,
  "tables": [
    {
      "full_name": "src.customers",
      "table_name": "customers",
      "group": "src",
      "key": "src.customers",
      "column_count": 5,
      "description": "Table customers in src group"
    }
  ]
}
```

### 5. List All Groups
- **GET** `/groups`
- **Description**: Get a list of all groups with their tables
- **Response**:
```json
{
  "total_groups": 3,
  "groups": [
    {
      "group_name": "src",
      "table_count": 3,
      "description": "Group src",
      "tables": [
        {
          "name": "customers",
          "full_name": "src.customers",
          "column_count": 5
        }
      ]
    }
  ]
}
```

### 6. DAG Statistics
- **GET** `/stats`
- **Description**: Get overall DAG statistics
- **Response**:
```json
{
  "total_groups": 3,
  "total_tables": 5,
  "total_columns": 23,
  "total_connections": 4,
  "groups_breakdown": {
    "src": {
      "tables": 3,
      "columns": 15
    },
    "stg": {
      "tables": 1,
      "columns": 7
    },
    "mart": {
      "tables": 1,
      "columns": 1
    }
  }
}
```

## 🔧 Usage Examples

### Using curl

```bash
# Health check
curl http://localhost:5000/health

# Get complete DAG
curl http://localhost:5000/dag

# Get table lineage
curl http://localhost:5000/table/enriched_orders/lineage

# List all tables
curl http://localhost:5000/tables

# Get statistics
curl http://localhost:5000/stats
```

### Using Python requests

```python
import requests
import json

base_url = "http://localhost:5000"

# Get complete DAG
response = requests.get(f"{base_url}/dag")
dag_data = response.json()

# Get table lineage
response = requests.get(f"{base_url}/table/enriched_orders/lineage")
lineage_data = response.json()

# Pretty print
print(json.dumps(lineage_data, indent=2))
```

## 🛠️ Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `404`: Table not found
- `500`: Internal server error

Error responses include details:
```json
{
  "error": "Table 'nonexistent' not found"
}
```

## 🎯 Key Features

- **Auto-initialization**: DAG is loaded automatically on startup
- **Flexible table lookup**: Supports both short names (`orders`) and full names (`src.orders`)
- **Rich metadata**: Includes descriptions, counts, and detailed lineage information
- **RESTful design**: Standard HTTP methods and status codes
- **JSON responses**: All responses are in JSON format
- **Error handling**: Proper error responses with meaningful messages
