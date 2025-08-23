# Example: How to target a different project

## Automatic Project Selection
The system automatically selects the first available project in alphabetical order from the `Projects/` directory. No manual configuration needed!

## Method 1: Use API Endpoints (Recommended - No Restart Required!)

### Check current project and available projects:
```bash
curl http://localhost:5000/project
```

### Switch to a different project:
```bash
curl -X POST http://localhost:5000/project/your-project-name
```

### Check health (shows current project):
```bash
curl http://localhost:5000/health
```

**Example workflow:**
```bash
# See what projects are available (auto-selected first one)
curl -s http://localhost:5000/project | jq

# Switch to specific project
curl -X POST http://localhost:5000/project/finance

# Verify the switch worked
curl -s http://localhost:5000/stats | jq '.total_tables'

# Switch to another project
curl -X POST http://localhost:5000/project/sample
```

## Method 2: Override with Environment Variable

Set `DAG_TARGET_PROJECT` to override the auto-selection:
```yaml
environment:
  - DAG_TARGET_PROJECT=your-project-name
```

## Adding new projects

1. Create a new folder under `Projects/`:
   ```
   Projects/
   ├── alpha/            # Will be auto-selected (first alphabetically)  
   ├── finance/          
   ├── sample/
   └── your-project/     # Your new project
       ├── table1.yml
       ├── table2.yml
       └── ...
   ```

2. The system will automatically detect and list it in available projects

3. Use the API to switch: `curl -X POST http://localhost:5000/project/your-project`

**Auto-selection behavior:**
- Projects are sorted alphabetically
- First project with valid YAML files is selected
- No null/empty projects - always has a valid default
- Shows available projects in logs: `🎯 Available projects: ['alpha', 'finance', 'sample']`
