# DAG Generator

A modern web application for visualizing and managing data pipeline dependencies using YAML configuration files. Built with FastAPI backend and React frontend.

![DAG Generator Demo](https://img.shields.io/badge/status-active-brightgreen)

## 🚀 Features

- **Interactive DAG Visualization**: View your data pipeline as an interactive directed acyclic graph
- **YAML-based Configuration**: Define tables, columns, and dependencies using simple YAML files
- **Column-level Lineage**: Track dependencies at the column level for detailed impact analysis
- **Multi-project Support**: Organize different data projects separately
- **Real-time Updates**: Hot reload YAML configurations without restarting
- **Responsive UI**: Modern React interface with ReactFlow for smooth graph interactions
- **Group-based Coloring**: Visual distinction between different table groups (src, stg, mart, etc.)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (recommended: Python 3.11)
- **Node.js 16+** (recommended: Node.js 18 or 20)
- **npm** or **yarn**

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/bmilliken/dag-generator.git
cd dag-generator
```

### 2. Backend Setup (Python/FastAPI)

#### Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

#### Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup (React/TypeScript)

```bash
cd Frontend
npm install
cd ..
```

### 4. Quick Start

The easiest way to start both servers is using the provided start script:

```bash
# Make the script executable (Linux/macOS)
chmod +x start.sh

# Run both backend and frontend
./start.sh
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs

### 5. Manual Setup (Alternative)

If you prefer to start services manually:

#### Start Backend Server:
```bash
cd Backend
../.venv/bin/python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend Server (in a new terminal):
```bash
cd Frontend
npm run dev
```

## 📁 Project Structure

```
dag-generator/
├── Backend/              # FastAPI backend
│   ├── api.py           # Main API endpoints
│   ├── models.py        # Pydantic data models
│   ├── loader.py        # YAML file loader
│   ├── graph_builder.py # Graph construction logic
│   ├── queries.py       # Lineage query functions
│   └── json_export.py   # Graph to JSON conversion
├── Frontend/            # React frontend
│   ├── src/
│   │   ├── App.tsx      # Main application component
│   │   ├── GraphView.tsx # DAG visualization component
│   │   ├── layout.ts    # Graph layout algorithms
│   │   ├── api.ts       # API client functions
│   │   └── types.ts     # TypeScript type definitions
│   └── package.json
├── Projects/            # YAML configuration files
│   ├── ecommerce/       # Example e-commerce project
│   └── finance/         # Example finance project
├── Groups/              # Shared table definitions
│   ├── Source/          # Source tables
│   ├── Staging/         # Staging tables
│   └── Mart/            # Mart tables
├── requirements.txt     # Python dependencies
├── start.sh            # Quick start script
└── README.md           # This file
```

## 📝 Configuration

### YAML Table Definitions

Tables are defined using YAML files with the following structure:

```yaml
group: src                    # Table group (src, stg, mart, etc.)
table: customers             # Table name
description: "Customer data from source system"
columns:
  - name: customer_id
    description: "Unique customer identifier"
    depends_on: []           # No dependencies for source columns
  - name: full_name
    description: "Customer full name"
    depends_on: [src.customers.first_name, src.customers.last_name]
```

### Column Dependencies

Dependencies are specified using the format: `group.table.column`

```yaml
columns:
  - name: customer_lifetime_value
    description: "Total value of all customer orders"
    depends_on: 
      - src.orders.customer_id
      - src.orders.total_amount
      - src.customers.customer_id
```

## 🎯 Usage

### 1. Viewing the Full DAG
- Open http://localhost:5173
- The full DAG will load automatically
- Use mouse wheel to zoom, click and drag to pan

### 2. Exploring Table Lineage
- Click on any table node to highlight its lineage
- View detailed column dependencies in the side panel
- Press `Escape` to clear highlighting

### 3. Adding New Tables
1. Create a new YAML file in the appropriate project directory
2. Define the table structure and column dependencies
3. Click "Reload" in the UI to refresh the visualization

### 4. Multi-project Support
- Add new projects by creating directories under `Projects/`
- Each project can have its own set of table definitions
- Switch between projects using the API endpoints

## 🔧 Development

### Backend Development

The backend uses FastAPI with the following key components:

- **Models**: Pydantic models for data validation
- **Graph Builder**: NetworkX for dependency graph construction  
- **API Endpoints**: RESTful APIs for graph data and lineage queries

### Frontend Development

The frontend is built with:

- **React 18** with TypeScript
- **ReactFlow** for interactive graph visualization
- **Vite** for fast development and building

### Key Commands

```bash
# Backend linting and testing
cd Backend
python -m pytest

# Frontend linting and building
cd Frontend
npm run lint
npm run build

# Type checking
npm run type-check
```

## 🌐 API Endpoints

- `GET /projects` - List available projects
- `GET /graph?project={project}&seed={table}` - Get graph data
- `GET /table-details?project={project}&table={table}` - Get table details
- `POST /reload` - Reload YAML configurations
- `GET /docs` - Interactive API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   - Change ports in `start.sh` or kill existing processes
   - Backend: `lsof -i :8000` then `kill -9 <PID>`
   - Frontend: `lsof -i :5173` then `kill -9 <PID>`

2. **Virtual environment issues**:
   - Ensure `.venv` is activated before installing packages
   - Recreate virtual environment if needed: `rm -rf .venv && python -m venv .venv`

3. **YAML parsing errors**:
   - Check YAML syntax and indentation
   - Ensure dependency format is `group.table.column`
   - Verify all referenced tables exist

4. **Frontend build issues**:
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

### Getting Help

- Check the [API documentation](http://localhost:8000/docs) when running
- Review example YAML files in `Projects/ecommerce/`
- Open an issue on GitHub for bugs or feature requests

## 🚧 Roadmap

- [ ] Database integration for table metadata
- [ ] Export functionality (PNG, SVG, PDF)
- [ ] Advanced filtering and search capabilities
- [ ] Performance optimizations for large graphs
- [ ] Dark mode theme
- [ ] Authentication and user management
