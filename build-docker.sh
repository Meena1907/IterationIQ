#!/bin/bash

# Build and run script for Spark Docker container

set -e  # Exit on any error

echo "🚀 Building Spark Docker Image..."

# Build the Docker image
docker build -t spark:latest .

echo "✅ Docker image built successfully!"

echo "📋 Available commands:"
echo "  Run with Docker Compose: docker-compose up -d"
echo "  Run directly: docker run -d --name spark -p 8080:8080 --env-file .env spark:latest"
echo "  View logs: docker logs spark"
echo "  Stop container: docker stop spark"

echo ""
echo "⚠️  Don't forget to:"
echo "  1. Copy .env.example to .env"
echo "  2. Fill in your Jira credentials in .env file"
echo "  3. Run the container with: docker-compose up -d"

echo ""
echo "🌐 Application will be available at: http://localhost:8080" 