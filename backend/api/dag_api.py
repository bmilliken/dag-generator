"""
REST API for DAG JSON Export

This module provides a REST API to expose the JSONExporter functionality
through HTTP endpoints.
"""

from flask import Flask, jsonify, request
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dag'))

from dag_assembler import DAGAssembler
from json_exporter import JSONExporter

app = Flask(__name__)

# ====================================
# CONFIGURATION - Auto-select first available project
# ====================================

def get_first_available_project():
    """Get the first available project from the Projects directory."""
    projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects")
    
    if not os.path.exists(projects_dir):
        return None
    
    # Get all directories in Projects folder
    available_projects = []
    for item in sorted(os.listdir(projects_dir)):
        project_path = os.path.join(projects_dir, item)
        if os.path.isdir(project_path):
            # Check if project has YAML files
            yaml_files = [f for f in os.listdir(project_path) if f.endswith('.yml') or f.endswith('.yaml')]
            if yaml_files:
                available_projects.append(item)
    
    return available_projects[0] if available_projects else None

# Set default project to first available, with fallback options
DEFAULT_PROJECT = get_first_available_project() or "finance"
TARGET_PROJECT = os.getenv("DAG_TARGET_PROJECT", DEFAULT_PROJECT)

print(f"🎯 Available projects: {sorted([d for d in os.listdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Projects')) if os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Projects', d))]) if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Projects')) else 'None'}")
print(f"🎯 Target project: {TARGET_PROJECT}")
# ====================================

# Global variables to store the assembled DAG
assembler = None
exporter = None
current_project = TARGET_PROJECT

def initialize_dag(project_name=None):
    """Initialize the DAG from the specified project."""
    global assembler, exporter, current_project
    
    # Use provided project name or current project
    if project_name:
        current_project = project_name
    
    # If current_project is None, try to find first available project
    if not current_project:
        current_project = get_first_available_project()
        if not current_project:
            raise FileNotFoundError("No valid projects found in Projects directory")
    
    try:
        assembler = DAGAssembler()
        # Assemble from the specified project
        project_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects", current_project)
        print(f"🎯 Loading project from: {project_path}")
        
        # Check if project directory exists
        if not os.path.exists(project_path):
            # Try to fallback to first available project
            fallback_project = get_first_available_project()
            if fallback_project and fallback_project != current_project:
                print(f"⚠️  Project '{current_project}' not found, falling back to '{fallback_project}'")
                current_project = fallback_project
                project_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects", current_project)
            else:
                raise FileNotFoundError(f"Project directory not found: {project_path}")
        
        assembler.assemble_from_project(project_path)
        
        # Create the JSON exporter
        exporter = JSONExporter(assembler.groups, assembler.tables, assembler.columns)
        
        print(f"✅ DAG initialized successfully for project: {current_project}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize DAG: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "DAG JSON API is running",
        "current_project": current_project
    })

@app.route('/project', methods=['GET'])
def get_current_project():
    """
    Get the currently loaded project information.
    
    Returns:
        JSON: Current project details and available projects
    """
    try:
        # List available projects in the Projects directory
        projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects")
        available_projects = []
        
        if os.path.exists(projects_dir):
            for item in os.listdir(projects_dir):
                project_path = os.path.join(projects_dir, item)
                if os.path.isdir(project_path):
                    available_projects.append(item)
        
        return jsonify({
            "current_project": current_project,
            "available_projects": sorted(available_projects),
            "initialized": exporter is not None
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get project info: {str(e)}"}), 500

@app.route('/project/<project_name>', methods=['POST'])
def set_project(project_name):
    """
    Set the current project and reload the DAG.
    
    Args:
        project_name: Name of the project folder under Projects/
    
    Returns:
        JSON: Success/error message and new project info
    """
    global current_project
    
    try:
        # Check if project exists
        projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects")
        project_path = os.path.join(projects_dir, project_name)
        
        if not os.path.exists(project_path):
            return jsonify({
                "error": f"Project '{project_name}' not found",
                "available_projects": [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
            }), 404
        
        # Initialize DAG with new project
        if initialize_dag(project_name):
            return jsonify({
                "message": f"Successfully switched to project '{project_name}'",
                "previous_project": current_project if current_project != project_name else None,
                "current_project": project_name,
                "total_tables": len(assembler.tables) if assembler else 0,
                "total_columns": len(assembler.columns) if assembler else 0
            })
        else:
            return jsonify({"error": f"Failed to initialize project '{project_name}'"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Failed to set project: {str(e)}"}), 500

@app.route('/dag', methods=['GET'])
def get_complete_dag():
    """
    Get the complete DAG structure.
    
    Returns:
        JSON: Complete DAG with all groups, tables, and connections
    """
    if exporter is None:
        return jsonify({"error": "DAG not initialized"}), 500
    
    try:
        dag_data = exporter.to_json()
        return jsonify(dag_data)
    except Exception as e:
        return jsonify({"error": f"Failed to export DAG: {str(e)}"}), 500

@app.route('/table/<table_name>/lineage', methods=['GET'])
def get_table_lineage(table_name):
    """
    Get complete lineage for a specific table.
    
    Args:
        table_name: Name of the table (supports both 'table_name' and 'group.table_name')
    
    Returns:
        JSON: Complete table lineage including tables, connections, and column details
    """
    if exporter is None:
        return jsonify({"error": "DAG not initialized"}), 500
    
    try:
        lineage_data = exporter.table_lineage_json(table_name)
        
        # Check if there was an error in the response
        if "error" in lineage_data:
            return jsonify(lineage_data), 404
        
        return jsonify(lineage_data)
    except Exception as e:
        return jsonify({"error": f"Failed to get table lineage: {str(e)}"}), 500

@app.route('/tables', methods=['GET'])
def list_tables():
    """
    List all available tables in the DAG.
    
    Returns:
        JSON: List of all tables with their full names and groups
    """
    if assembler is None:
        return jsonify({"error": "DAG not initialized"}), 500
    
    try:
        tables_list = []
        for table_key, table in assembler.tables.items():
            tables_list.append({
                "full_name": table.get_full_name(),
                "table_name": table.name,
                "group": table.group,
                "key": table_key,
                "column_count": len(table.columns),
                "description": table.description
            })
        
        # Sort by full name
        tables_list.sort(key=lambda x: x["full_name"])
        
        return jsonify({
            "total_tables": len(tables_list),
            "tables": tables_list
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list tables: {str(e)}"}), 500

@app.route('/groups', methods=['GET'])
def list_groups():
    """
    List all groups with their tables.
    
    Returns:
        JSON: List of all groups and their tables
    """
    if assembler is None:
        return jsonify({"error": "DAG not initialized"}), 500
    
    try:
        groups_list = []
        for group_name, group in assembler.groups.items():
            group_info = {
                "group_name": group_name,
                "table_count": len(group.tables),
                "description": group.description,
                "tables": [
                    {
                        "name": table.name,
                        "full_name": table.get_full_name(),
                        "column_count": len(table.columns)
                    }
                    for table in sorted(group.tables, key=lambda t: t.name)
                ]
            }
            groups_list.append(group_info)
        
        # Sort by group name
        groups_list.sort(key=lambda x: x["group_name"])
        
        return jsonify({
            "total_groups": len(groups_list),
            "groups": groups_list
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list groups: {str(e)}"}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get DAG statistics.
    
    Returns:
        JSON: Statistics about the DAG (table count, column count, etc.)
    """
    if assembler is None:
        return jsonify({"error": "DAG not initialized"}), 500
    
    try:
        # Count connections
        connection_count = 0
        for table in assembler.tables.values():
            connection_count += len(table.dependencies)
        
        stats = {
            "total_groups": len(assembler.groups),
            "total_tables": len(assembler.tables),
            "total_columns": len(assembler.columns),
            "total_connections": connection_count,
            "groups_breakdown": {}
        }
        
        # Group breakdown
        for group_name, group in assembler.groups.items():
            table_count = len(group.tables)
            column_count = sum(len(table.columns) for table in group.tables)
            
            stats["groups_breakdown"][group_name] = {
                "tables": table_count,
                "columns": column_count
            }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 Starting DAG JSON API server...")
    
    # Initialize the DAG on startup
    if not initialize_dag():
        print("❌ Failed to initialize DAG. Exiting...")
        exit(1)
    
    print("\n📊 Available Endpoints:")
    print("  GET  /health                    - Health check")
    print("  GET  /project                   - Get current project info")
    print("  POST /project/<name>            - Switch to different project")
    print("  GET  /dag                       - Complete DAG structure")
    print("  GET  /table/<name>/lineage      - Table lineage (supports both 'table' and 'group.table')")
    print("  GET  /tables                    - List all tables")
    print("  GET  /groups                    - List all groups")
    print("  GET  /stats                     - DAG statistics")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
