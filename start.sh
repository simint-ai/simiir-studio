#!/bin/bash

# Start script for SimIIR API

echo "Starting SimIIR API..."

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install poetry first:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Create necessary directories
mkdir -p outputs
mkdir -p logs

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please review and update .env file with your configuration."
fi

# Initialize database
echo "Initializing database..."
poetry run python -c "
import asyncio
from simiir_api.database import init_db

async def main():
    await init_db()
    print('Database initialized successfully!')

asyncio.run(main())
"

# Start the API server
echo "Starting API server..."
poetry run simiir-api

