FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY frameworks/ ./frameworks/
COPY data/ ./data/
COPY knowledge/ ./knowledge/
COPY config.py ./config.py
COPY errors.py ./errors.py
COPY health.py ./health.py
COPY logging_config.py ./logging_config.py
COPY middleware/ ./middleware/

# Set Python path so backend imports resolve
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
