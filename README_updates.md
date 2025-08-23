# DAG Generator - Finance Project Updates

## Changes Made

### 1. Added Descriptions to Source Columns

Updated all source YAML files in the `Projects/finance/` directory to include meaningful descriptions for each column:

#### `src_customers.yml`
- `customer_id`: "Unique identifier for each customer"
- `customer_name`: "Full name of the customer"  
- `customer_email`: "Email address of the customer"
- `customer_segment`: "Customer segmentation category (e.g., Premium, Standard, Basic)"
- `registration_date`: "Date when the customer registered with the service"

#### `src_orders.yml`
- `order_id`: "Unique identifier for each order"
- `user_id`: "Foreign key reference to the customer who placed the order"
- `order_date`: "Date and time when the order was placed"
- `total_amount`: "Total monetary value of the order including taxes and fees"
- `status`: "Current status of the order (e.g., pending, shipped, delivered, cancelled)"

#### `src_order_items.yml`
- `item_id`: "Unique identifier for each order item line"
- `order_id`: "Foreign key reference to the order this item belongs to"
- `product_id`: "Foreign key reference to the product being ordered"
- `quantity`: "Number of units of the product ordered"
- `unit_price`: "Price per unit of the product at the time of order"

### 2. Created JSON Schema for Validation

Created `schema/table_schema.json` with comprehensive validation rules:

#### Required Fields
- `group`: Must be one of "src", "stg", "int", "mart"
- `table`: Table name following naming conventions
- `columns`: Array of column definitions

#### Column Schema
Each column must have:
- `name`: Column name (required)
- `depends_on`: Array of dependencies (required, empty for source columns)
- `description`: Optional description
- `data_type`: Optional data type specification
- `nullable`: Whether column accepts null values
- `primary_key`: Whether column is part of primary key
- `foreign_key`: Reference to another table's column

#### Validation Rules
- Group names must be valid enum values
- Table and column names must follow identifier patterns
- Dependencies must be fully qualified (group.table.column format)
- No duplicate dependencies allowed

### 3. Created Validation Scripts

#### `validate_yaml.py` (Full Validation)
- Requires `pyyaml` and `jsonschema` packages
- Validates YAML files against the JSON schema
- Provides detailed error reporting
- Usage: `python validate_yaml.py Projects/finance`

#### `validate_basic.py` (Basic Validation)
- Lightweight validation without external dependencies
- Checks basic structure and required fields
- Good for quick validation during development

#### `requirements.txt`
Contains required Python packages:
- `pyyaml>=6.0`
- `jsonschema>=4.0.0`

## Usage

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Validate Finance Project
```bash
python validate_yaml.py Projects/finance
```

### Basic Structure Check
```bash
python validate_basic.py
```

## Schema Benefits

1. **Consistency**: Ensures all YAML files follow the same structure
2. **Validation**: Catches syntax errors and missing required fields  
3. **Documentation**: Schema serves as documentation for the expected format
4. **IDE Support**: JSON Schema enables autocomplete and validation in IDEs
5. **CI/CD Integration**: Can be integrated into build pipelines for automated validation

## Next Steps

1. Apply the schema to other project directories (ecommerce)
2. Add data type validation for better type safety
3. Implement cross-reference validation (ensure dependencies exist)
4. Create automated tests using the validation framework
