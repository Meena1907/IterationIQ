#!/bin/bash

# Build and run script for Jira Hub Docker container

set -e  # Exit on any error

echo "🚀 Building Jira Hub Docker Image..."

# Build the Docker image
docker build -t jira-hub:latest .

echo "✅ Docker image built successfully!"

echo "📋 Available commands:"
echo "  Run with Docker Compose: docker-compose up -d"
echo "  Run directly: docker run -d --name jira-hub -p 8080:8080 --env-file .env jira-hub:latest"
echo "  View logs: docker logs jira-hub"
echo "  Stop container: docker stop jira-hub"

echo ""
echo "⚠️  Don't forget to:"
echo "  1. Copy .env.example to .env"
echo "  2. Fill in your Jira credentials in .env file"
echo "  3. Run the container with: docker-compose up -d"

echo ""
echo "🌐 Application will be available at: http://localhost:8080" 