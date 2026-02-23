# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the native Cloud Run logs
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create and change to the app directory.
WORKDIR /app

# Copy only the configuration files first to leverage Docker cache
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY . .

# Install the app itself (this time including the source code)
RUN pip install --no-cache-dir .

# Run the web service on container startup using Uvicorn.
# Cloud Run automatically sets the PORT environment variable.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
