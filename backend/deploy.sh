#!/bin/bash
# Deployment script for Rice Course Assistant Backend

echo "🚀 Starting deployment..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "❌ Error: data directory not found. Please ensure data files are in the backend/data directory."
    exit 1
fi

# Check if required data files exist
required_files=(
    "data/organized/rice_organized_data.json"
    "data/raw/rice_courses_202610_with_instructors.json"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file $file not found."
        exit 1
    fi
done

echo "✅ All required files found"

# Test app import
echo "🧪 Testing app import..."
python -c "import app; print('✅ App imported successfully')"

if [ $? -eq 0 ]; then
    echo "✅ App import test passed"
else
    echo "❌ App import test failed"
    exit 1
fi

# Start Gunicorn
echo "🚀 Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 300 --log-level debug app:app 