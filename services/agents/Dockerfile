FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/agents/src ./src
COPY packages/shared-types/dist ./types

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the agent service
CMD ["python", "-m", "src.main"]
