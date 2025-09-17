# Multi-stage Docker build for React frontend + Flask backend

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY frontend/src ./src
COPY frontend/public ./public

# Build React app
RUN npm run build

# Stage 2: Build Python backend
FROM python:3.9-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev curl

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY app.py .
COPY scripts/ ./scripts/
COPY settings_manager.py .
COPY ai_sprint_insights.py .
COPY user_tracking.py .
COPY set_jira_creds.sh .

# Copy built React app from frontend stage
COPY --from=frontend-builder /app/frontend/build ./static

# Create directories for persistent data
RUN mkdir -p temp_screenshots data

EXPOSE 8080

CMD ["python", "app.py"]
