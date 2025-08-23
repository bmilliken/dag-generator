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

# Global variables to store the assembled DAG
assembler = None
exporter = None

def initialize_dag():
    """Initialize the DAG from the finance project."""
    global assembler, exporter
    
    try:
        assembler = DAGAssembler()
        # Assemble from the finance project (you can make this configurable)
        project_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Projects", "finance")
        assembler.assemble_from_project(project_path)
        
        # Create the JSON exporter
        exporter = JSONExporter(assembler.groups, assembler.tables, assembler.columns)
        
        print("✅ DAG initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize DAG: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "DAG JSON API is running"
    })

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
    print("  GET  /dag                       - Complete DAG structure")
    print("  GET  /table/<name>/lineage      - Table lineage (supports both 'table' and 'group.table')")
    print("  GET  /tables                    - List all tables")
    print("  GET  /groups                    - List all groups")
    print("  GET  /stats                     - DAG statistics")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
