#!/bin/bash

# Docker Setup Validation Script
# Tests the Docker configuration without actually building

echo "🔍 Validating Docker setup for DAG Generator..."

# Check required files exist
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    ".dockerignore"
    "requirements.txt"
    "api/dag_api.py"
)

echo "📁 Checking required files..."
all_present=true
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        all_present=false
    fi
done

# Check directories
required_dirs=(
    "api"
    "dag" 
    "objects"
    "schema"
    "Projects"
)

echo ""
echo "📂 Checking required directories..."
for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ (missing)"
        all_present=false
    fi
done

# Check Python dependencies
echo ""
echo "🐍 Checking Python requirements..."
if grep -qi "flask" requirements.txt; then
    echo "  ✅ Flask dependency found"
else
    echo "  ❌ Flask dependency missing"
    all_present=false
fi

# Check API configuration
echo ""
echo "⚙️  Checking API configuration..."
if grep -q "host='0.0.0.0'" api/dag_api.py; then
    echo "  ✅ API configured for Docker (0.0.0.0 binding)"
else
    echo "  ❌ API not configured for Docker"
    all_present=false
fi

# Check dockerignore
echo ""
echo "🚫 Checking .dockerignore..."
if [[ -f ".dockerignore" ]]; then
    echo "  ✅ .dockerignore present"
    if grep -q "__pycache__" .dockerignore; then
        echo "  ✅ Python cache excluded"
    else
        echo "  ⚠️  Python cache not excluded"
    fi
else
    echo "  ❌ .dockerignore missing"
fi

echo ""
if [[ "$all_present" == true ]]; then
    echo "✅ Docker setup validation PASSED"
    echo ""
    echo "🐳 Ready to build with:"
    echo "   docker build -t dag-generator-api ."
    echo ""
    echo "🚀 Ready to run with:"
    echo "   docker-compose up -d"
    echo ""
    echo "📖 See DOCKER_README.md for full documentation"
else
    echo "❌ Docker setup validation FAILED"
    echo "Please fix the missing components above"
fi
