#!/bin/bash

# Script to push cloud-finops to GitHub
# Repository: https://github.com/yksanjo/cloud-finops.git

set -e

echo "🚀 Pushing cloud-finops to GitHub..."

# Navigate to the cloud-finops directory
cd "$(dirname "$0")"

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "🔗 Adding remote repository..."
    git remote add origin https://github.com/yksanjo/cloud-finops.git
else
    echo "✅ Remote repository already configured"
fi

# Add all files
echo "📝 Adding files..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Initial commit: Cloud FinOps Optimizer

- Multi-cloud support (AWS, Azure, GCP)
- Cost analysis and resource optimization
- Automated optimization recommendations
- Comprehensive reporting (text, JSON, CSV, HTML)
- CLI interface and Python API
- Example scripts and documentation"
fi

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git push -u origin main

echo "✅ Successfully pushed to https://github.com/yksanjo/cloud-finops.git"
echo ""
echo "🎉 Your Cloud FinOps Optimizer is now on GitHub!"

