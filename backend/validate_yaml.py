"""
YAML Schema Validator for DAG Generator

This script validates table definition YAML files against the defined JSON schema
to ensure they follow the correct structure and contain valid data.
"""

import json
import yaml
import jsonschema
from pathlib import Path
from typing import List, Dict, Any
import sys


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the JSON schema from file."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def load_yaml_file(yaml_path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def validate_yaml_file(yaml_path: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single YAML file against the schema.
    
    Returns:
        List of validation errors (empty if valid)
    """
    try:
        yaml_data = load_yaml_file(yaml_path)
        jsonschema.validate(yaml_data, schema)
        return []
    except jsonschema.ValidationError as e:
        return [f"Validation error in {yaml_path}: {e.message}"]
    except yaml.YAMLError as e:
        return [f"YAML syntax error in {yaml_path}: {e}"]
    except Exception as e:
        return [f"Error processing {yaml_path}: {e}"]


def validate_project_yamls(project_path: str, schema_path: str) -> Dict[str, List[str]]:
    """
    Validate all YAML files in a project directory against the schema.
    
    Returns:
        Dictionary mapping file paths to lists of errors
    """
    schema = load_schema(schema_path)
    project_dir = Path(project_path)
    results = {}
    
    # Find all YAML files in the project
    yaml_files = list(project_dir.glob("*.yml")) + list(project_dir.glob("*.yaml"))
    
    for yaml_file in yaml_files:
        errors = validate_yaml_file(str(yaml_file), schema)
        results[str(yaml_file)] = errors
    
    return results


def print_validation_results(results: Dict[str, List[str]]) -> None:
    """Print validation results in a readable format."""
    total_files = len(results)
    valid_files = sum(1 for errors in results.values() if not errors)
    invalid_files = total_files - valid_files
    
    print(f"Validation Results:")
    print(f"==================")
    print(f"Total files: {total_files}")
    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {invalid_files}")
    print()
    
    if invalid_files > 0:
        print("Validation Errors:")
        print("------------------")
        for file_path, errors in results.items():
            if errors:
                print(f"\n{file_path}:")
                for error in errors:
                    print(f"  - {error}")
    else:
        print("All files are valid! ✅")


def main():
    """Main function to run the validator."""
    if len(sys.argv) < 2:
        print("Usage: python validate_yaml.py <project_path> [schema_path]")
        print("Example: python validate_yaml.py Projects/finance")
        sys.exit(1)
    
    project_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else "schema/table_schema.json"
    
    if not Path(project_path).exists():
        print(f"Error: Project path '{project_path}' does not exist.")
        sys.exit(1)
    
    if not Path(schema_path).exists():
        print(f"Error: Schema file '{schema_path}' does not exist.")
        sys.exit(1)
    
    print(f"Validating YAML files in: {project_path}")
    print(f"Using schema: {schema_path}")
    print()
    
    results = validate_project_yamls(project_path, schema_path)
    print_validation_results(results)
    
    # Exit with error code if any files are invalid
    invalid_count = sum(1 for errors in results.values() if errors)
    sys.exit(invalid_count)


if __name__ == "__main__":
    main()
