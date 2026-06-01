# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP run.py
ENV FLASK_ENV production

# Set the working directory in the container
WORKDIR /app

# Install system build dependencies for wheel compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python package dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the docker workspace
COPY . .

# Expose server port 5000
EXPOSE 5000

# Start the application using Gunicorn multi-threaded workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app", "--workers", "4", "--threads", "2"]
