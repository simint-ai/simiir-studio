FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==1.7.1

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Install the package
RUN poetry install --no-interaction --no-ansi

# Create directories
RUN mkdir -p /app/outputs /app/logs /app/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "simiir-api"]

