# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Start backend and frontend
CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
    streamlit run streamlit.py --server.port 8501 --server.address 0.0.0.0