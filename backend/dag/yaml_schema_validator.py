"""
YAML Schema Validator for DAG Generator

This module provides comprehensive YAML schema validation that runs before
any object construction to ensure all YAML files are valid and conform
to the expected structure.
"""

import json
import yaml
import jsonschema
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys
import os


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class YAMLSchemaValidator:
    """
    Validates YAML files against the defined JSON schema before DAG assembly.
    """
    
    def __init__(self, schema_path: str = None):
        """
        Initialize the validator with the schema.
        
        Args:
            schema_path: Path to the JSON schema file. If None, uses default location.
        """
        if schema_path is None:
            # Default to the schema directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(current_dir, "..", "schema", "table_schema.json")
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from file."""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in schema file {self.schema_path}: {e}")
    
    def _load_yaml_file(self, yaml_path: str) -> Dict[str, Any]:
        """Load a YAML file and return its contents."""
        try:
            with open(yaml_path, 'r') as f:
                content = yaml.safe_load(f)
                if content is None:
                    raise ValidationError(f"YAML file {yaml_path} is empty or contains no data")
                return content
        except yaml.YAMLError as e:
            raise ValidationError(f"YAML syntax error in {yaml_path}: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading YAML file {yaml_path}: {e}")
    
    def validate_single_file(self, yaml_path: str) -> List[str]:
        """
        Validate a single YAML file against the schema.
        
        Args:
            yaml_path: Path to the YAML file to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        try:
            yaml_data = self._load_yaml_file(yaml_path)
            jsonschema.validate(yaml_data, self.schema)
            return []
        except jsonschema.ValidationError as e:
            error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            return [f"Schema validation error at {error_path}: {e.message}"]
        except ValidationError as e:
            return [str(e)]
        except Exception as e:
            return [f"Unexpected error validating {yaml_path}: {e}"]
    
    def validate_project_files(self, project_path: str) -> Dict[str, List[str]]:
        """
        Validate all YAML files in a project directory.
        
        Args:
            project_path: Path to the project directory containing YAML files
            
        Returns:
            Dictionary mapping file paths to lists of errors
        """
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            raise ValidationError(f"Project directory '{project_path}' does not exist")
        
        # Find all YAML files
        yaml_files = list(project_dir.glob("*.yml")) + list(project_dir.glob("*.yaml"))
        
        if not yaml_files:
            raise ValidationError(f"No YAML files found in project directory: {project_path}")
        
        results = {}
        for yaml_file in yaml_files:
            errors = self.validate_single_file(str(yaml_file))
            results[str(yaml_file)] = errors
        
        return results
    
    def validate_project_files_strict(self, project_path: str) -> List[Dict[str, Any]]:
        """
        Validate all YAML files in a project directory and return valid YAML data.
        
        Args:
            project_path: Path to the project directory containing YAML files
            
        Returns:
            List of valid YAML file data
            
        Raises:
            ValidationError: If any file fails validation
        """
        results = self.validate_project_files(project_path)
        
        # Check for any validation errors
        all_errors = []
        for file_path, errors in results.items():
            if errors:
                all_errors.extend([f"{file_path}: {error}" for error in errors])
        
        if all_errors:
            error_message = "YAML validation failed:\n" + "\n".join(all_errors)
            raise ValidationError(error_message)
        
        # If all files are valid, load and return the YAML data
        valid_yaml_data = []
        project_dir = Path(project_path)
        yaml_files = list(project_dir.glob("*.yml")) + list(project_dir.glob("*.yaml"))
        
        for yaml_file in sorted(yaml_files):
            yaml_data = self._load_yaml_file(str(yaml_file))
            valid_yaml_data.append(yaml_data)
        
        return valid_yaml_data
    
    def get_validation_summary(self, results: Dict[str, List[str]]) -> Tuple[int, int, int]:
        """
        Get summary statistics from validation results.
        
        Args:
            results: Results from validate_project_files
            
        Returns:
            Tuple of (total_files, valid_files, invalid_files)
        """
        total_files = len(results)
        invalid_files = sum(1 for errors in results.values() if errors)
        valid_files = total_files - invalid_files
        
        return total_files, valid_files, invalid_files
    
    def print_validation_results(self, results: Dict[str, List[str]], verbose: bool = True) -> None:
        """
        Print validation results in a readable format.
        
        Args:
            results: Results from validate_project_files
            verbose: Whether to show detailed error messages
        """
        total_files, valid_files, invalid_files = self.get_validation_summary(results)
        
        print(f"YAML Schema Validation Results:")
        print(f"{'=' * 35}")
        print(f"Total files processed: {total_files}")
        print(f"Valid files: {valid_files}")
        print(f"Invalid files: {invalid_files}")
        
        if invalid_files > 0:
            print(f"\n❌ Validation failed for {invalid_files} file(s)")
            if verbose:
                print(f"\nDetailed Errors:")
                print(f"{'-' * 20}")
                for file_path, errors in results.items():
                    if errors:
                        print(f"\n📁 {file_path}:")
                        for error in errors:
                            print(f"   ❌ {error}")
        else:
            print(f"\n✅ All files passed validation!")


def main():
    """Standalone script to validate YAML files."""
    if len(sys.argv) < 2:
        print("Usage: python yaml_schema_validator.py <project_path> [schema_path]")
        print("Example: python yaml_schema_validator.py ../projects/finance")
        sys.exit(1)
    
    project_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        validator = YAMLSchemaValidator(schema_path)
        results = validator.validate_project_files(project_path)
        validator.print_validation_results(results)
        
        # Exit with error code if any files are invalid
        _, _, invalid_files = validator.get_validation_summary(results)
        sys.exit(invalid_files)
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
