"""
REST API for DAG JSON Export

This module provides a REST API to expose the JSONExporter functionality
through HTTP endpoints.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))  # Add current directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dag'))

from dag.dag_assembler import DAGAssembler
from json_exporter import JSONExporter  # Now in same directory
from file_watcher import file_watcher   # Now in same directory

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ====================================
# CONFIGURATION - Auto-select first available project
# ====================================

def get_first_available_project():
    """Get the first available project from the projects directory."""
    # Check if we're running in Docker (projects mounted at /app/projects)
    if os.path.exists("/app/projects"):
        projects_dir = "/app/projects"
    else:
        # Local development path
        projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "projects")
    
    if not os.path.exists(projects_dir):
        return None
    
    # Get all directories in Projects folder
    available_projects = []
    for item in sorted(os.listdir(projects_dir)):
        project_path = os.path.join(projects_dir, item)
        if os.path.isdir(project_path):
            # Check if project has YAML files (recursively check subdirectories too)
            has_yaml = False
            for root, dirs, files in os.walk(project_path):
                yaml_files = [f for f in files if f.endswith('.yml') or f.endswith('.yaml')]
                if yaml_files:
                    has_yaml = True
                    break
            
            if has_yaml:
                available_projects.append(item)
    
    return available_projects[0] if available_projects else None

# Set default project to first available, with fallback options
DEFAULT_PROJECT = get_first_available_project() or "finance"
TARGET_PROJECT = os.getenv("DAG_TARGET_PROJECT", DEFAULT_PROJECT)

def get_projects_dir():
    """Get the projects directory path."""
    if os.path.exists("/app/projects"):
        return "/app/projects"
    else:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "projects")

projects_dir = get_projects_dir()
available_projects = []
if os.path.exists(projects_dir):
    available_projects = sorted([d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))])

print(f"🎯 Available projects: {available_projects}")
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
        project_path = os.path.join(get_projects_dir(), current_project)
        print(f"🎯 Loading project from: {project_path}")
        
        # Check if project directory exists
        if not os.path.exists(project_path):
            # Try to fallback to first available project
            fallback_project = get_first_available_project()
            if fallback_project and fallback_project != current_project:
                print(f"⚠️  Project '{current_project}' not found, falling back to '{fallback_project}'")
                current_project = fallback_project
                project_path = os.path.join(get_projects_dir(), current_project)
            else:
                raise FileNotFoundError(f"Project directory not found: {project_path}")
        
        assembler.assemble_from_project(project_path)
        
        # Create the JSON exporter
        exporter = JSONExporter(assembler.groups, assembler.tables, assembler.columns)
        
        # Clear any pending changes for this project since we just reloaded it
        file_watcher.clear_pending_changes(current_project)
        
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
        # List available projects in the projects directory
        projects_dir = get_projects_dir()
        available_projects = []
        
        print(f"🔍 Debug: projects_dir = {projects_dir}")
        print(f"🔍 Debug: exists = {os.path.exists(projects_dir)}")
        
        if os.path.exists(projects_dir):
            for item in os.listdir(projects_dir):
                project_path = os.path.join(projects_dir, item)
                print(f"🔍 Debug: checking item = {item}, path = {project_path}")
                if os.path.isdir(project_path):
                    try:
                        # Check if project has YAML files (recursively check subdirectories too)
                        has_yaml = False
                        yaml_files_found = []
                        for root, dirs, files in os.walk(project_path):
                            yaml_files = [f for f in files if f.endswith('.yml') or f.endswith('.yaml')]
                            if yaml_files:
                                yaml_files_found.extend([f"{os.path.relpath(root, project_path)}/{f}" for f in yaml_files])
                                has_yaml = True
                        
                        print(f"🔍 Debug: {item} has YAML files: {has_yaml} - files: {yaml_files_found}")
                        if has_yaml:
                            available_projects.append(item)
                    except Exception as e:
                        print(f"⚠️  Error checking project {item}: {e}")
        
        print(f"🔍 Debug: final available_projects = {available_projects}")
        
        return jsonify({
            "current_project": current_project,
            "available_projects": sorted(available_projects),
            "initialized": exporter is not None,
            "has_pending_changes": file_watcher.has_pending_changes(current_project) if current_project else False,
            "pending_changes_count": len(file_watcher.get_pending_changes(current_project)) if current_project else 0
        })
    except Exception as e:
        print(f"❌ Error in get_current_project: {e}")
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
        projects_dir = get_projects_dir()
        project_path = os.path.join(projects_dir, project_name)
        
        if not os.path.exists(project_path):
            # Get list of available projects for error response
            available_projects = []
            if os.path.exists(projects_dir):
                for item in os.listdir(projects_dir):
                    if os.path.isdir(os.path.join(projects_dir, item)):
                        # Check if project has YAML files (recursively)
                        project_item_path = os.path.join(projects_dir, item)
                        has_yaml = False
                        for root, dirs, files in os.walk(project_item_path):
                            yaml_files = [f for f in files if f.endswith('.yml') or f.endswith('.yaml')]
                            if yaml_files:
                                has_yaml = True
                                break
                        if has_yaml:
                            available_projects.append(item)
            
            return jsonify({
                "error": f"Project '{project_name}' not found",
                "available_projects": available_projects
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

@app.route('/refresh', methods=['POST'])
def refresh_project():
    """
    Refresh the current project by reloading the DAG from disk.
    
    Returns:
        JSON: Success/error message and updated project info
    """
    if not current_project:
        return jsonify({"error": "No project loaded"}), 400
    
    try:
        pending_changes = file_watcher.get_pending_changes(current_project)
        print(f"🔄 Refreshing project '{current_project}' with {len(pending_changes)} pending changes")
        
        # Reinitialize the DAG
        if initialize_dag(current_project):
            return jsonify({
                "message": f"Successfully refreshed project '{current_project}'",
                "project": current_project,
                "total_tables": len(assembler.tables) if assembler else 0,
                "total_columns": len(assembler.columns) if assembler else 0,
                "changes_applied": len(pending_changes),
                "has_pending_changes": False
            })
        else:
            return jsonify({"error": f"Failed to refresh project '{current_project}'"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to refresh project: {str(e)}"}), 500

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
    
    # Start file watching
    projects_dir = get_projects_dir()
    file_watcher.start_watching(projects_dir)
    
    print("\n📊 Available Endpoints:")
    print("  GET  /health                    - Health check")
    print("  GET  /project                   - Get current project info")
    print("  POST /project/<name>            - Switch to different project")
    print("  POST /refresh                   - Refresh current project from disk")
    print("  GET  /dag                       - Complete DAG structure")
    print("  GET  /table/<name>/lineage      - Table lineage (supports both 'table' and 'group.table')")
    print("  GET  /tables                    - List all tables")
    print("  GET  /groups                    - List all groups")
    print("  GET  /stats                     - DAG statistics")
    
    print(f"\n🌐 Server starting on http://localhost:5002")
    print("📁 File watching enabled - changes will be tracked but not auto-applied")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5002)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        file_watcher.stop_watching()
    except Exception as e:
        print(f"❌ Error running server: {e}")
        file_watcher.stop_watching()
