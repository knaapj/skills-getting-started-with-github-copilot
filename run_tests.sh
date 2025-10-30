#!/bin/bash
# Test runner script for Mergington High School Activities API

echo "Running FastAPI Tests..."
echo "========================"

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed successfully!"
    echo "🎉 Test coverage: 100%"
else
    echo ""
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi