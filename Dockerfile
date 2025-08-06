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

# Copy application code
COPY . .

# Create directories for persistent data
RUN mkdir -p temp_screenshots data

EXPOSE 8080

CMD ["python", "app.py"]
