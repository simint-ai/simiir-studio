# SimIIR API - Command Reference Cheat Sheet

Quick reference for common commands and API calls.

## Setup & Startup

```bash
# Quick start (recommended)
./start.sh

# Or manual start
poetry install
poetry run simiir-api

# With auto-reload (development)
poetry run uvicorn simiir_api.main:app --reload

# Using Make
make install
make run
make dev
```

## Docker Commands

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

## API Commands (cURL)

### Create Simulation
```bash
curl -X POST http://localhost:8000/simulations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Simulation",
    "description": "My test",
    "config_content": "'$(cat examples/example_simulation_config.xml)'",
    "users": ["user1", "user2"],
    "topics": ["303", "307"]
  }'
```

### List All Simulations
```bash
curl http://localhost:8000/simulations/
```

### List Running Simulations
```bash
curl "http://localhost:8000/simulations/?status=running"
```

### Get Simulation Status
```bash
curl http://localhost:8000/simulations/sim_abc123
```

### Start Simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

### Pause Simulation (with checkpoint)
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause", "checkpoint_before_action": true}'
```

### Resume Simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}'
```

### Stop Simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'
```

### Get Results
```bash
curl http://localhost:8000/simulations/sim_abc123/results
```

### Get Logs (all)
```bash
curl http://localhost:8000/simulations/sim_abc123/logs
```

### Get Logs (last 50 lines)
```bash
curl "http://localhost:8000/simulations/sim_abc123/logs?tail=50"
```

### List Checkpoints
```bash
curl http://localhost:8000/simulations/sim_abc123/checkpoints
```

### Update Simulation (pending only)
```bash
curl -X PATCH http://localhost:8000/simulations/sim_abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "description": "Updated description"
  }'
```

### Delete Simulation
```bash
curl -X DELETE http://localhost:8000/simulations/sim_abc123
```

## Python Commands

### Using requests
```python
import requests

BASE = "http://localhost:8000"

# Create
sim = requests.post(f"{BASE}/simulations/", json={...}).json()

# Start
requests.post(f"{BASE}/simulations/{sim['id']}/control", 
              json={"action": "start"})

# Status
status = requests.get(f"{BASE}/simulations/{sim['id']}").json()

# Logs
logs = requests.get(f"{BASE}/simulations/{sim['id']}/logs", 
                    params={"tail": 50}).json()

# Results
results = requests.get(f"{BASE}/simulations/{sim['id']}/results").json()
```

### Run example script
```bash
python examples/api_usage.py
```

## Testing Commands

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test
poetry run pytest tests/test_api.py::test_create_simulation

# Run with coverage
poetry run pytest --cov=simiir_api
```

## Development Commands

```bash
# Format code
poetry run black src/ tests/
# Or
make format

# Lint code
poetry run ruff check src/ tests/
# Or
make lint

# Clean up
make clean
```

## Database Commands

```bash
# Initialize database (done automatically by start.sh)
poetry run python -c "
import asyncio
from simiir_api.database import init_db
asyncio.run(init_db())
"

# Interactive database shell (SQLite)
sqlite3 simiir_api.db
```

## Log Commands

```bash
# View API logs (real-time)
tail -f logs/simiir_api.log

# View simulation logs
tail -f outputs/sim_abc123/simulation.log

# View last 100 lines
tail -n 100 logs/simiir_api.log
```

## Configuration Commands

```bash
# Create .env from example
cp .env.example .env

# Edit configuration
nano .env

# View current config
cat .env
```

## Monitoring Commands

```bash
# Check if API is running
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/

# Check process
ps aux | grep simiir-api

# Check port
lsof -i :8000
```

## Cleanup Commands

```bash
# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clean outputs
rm -rf outputs/*

# Clean logs
rm -rf logs/*

# Clean database (careful!)
rm simiir_api.db

# Full clean
make clean
```

## Useful One-Liners

```bash
# Create and start simulation in one go
SIM_ID=$(curl -s -X POST http://localhost:8000/simulations/ \
  -H "Content-Type: application/json" \
  -d @create_sim.json | jq -r '.id') && \
curl -X POST http://localhost:8000/simulations/$SIM_ID/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# Get status of all running simulations
curl -s "http://localhost:8000/simulations/?status=running" | jq

# Watch simulation status (updates every 2 seconds)
watch -n 2 "curl -s http://localhost:8000/simulations/sim_abc123 | jq '.status, .progress_percentage'"

# Export all simulations to JSON
curl -s http://localhost:8000/simulations/ | jq > all_simulations.json

# Count simulations by status
curl -s http://localhost:8000/simulations/ | jq 'group_by(.status) | map({status: .[0].status, count: length})'
```

## Environment Variables

```bash
# Override port
PORT=8001 poetry run simiir-api

# Override host
HOST=127.0.0.1 poetry run simiir-api

# Enable debug
DEBUG=true poetry run simiir-api

# Custom database
DATABASE_URL=sqlite+aiosqlite:///./custom.db poetry run simiir-api
```

## URLs

- **API Root**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## File Locations

```
Configuration:     .env
Database:          simiir_api.db
API Logs:          logs/simiir_api.log
Simulation Output: outputs/{simulation_id}/
Checkpoints:       outputs/{simulation_id}/checkpoints/
Config Files:      outputs/{simulation_id}/config.xml
```

## Quick Troubleshooting

```bash
# Check if port is in use
lsof -i :8000

# Kill process on port 8000
kill $(lsof -t -i:8000)

# Check logs for errors
grep ERROR logs/simiir_api.log

# Verify database exists
ls -lh simiir_api.db

# Check simIIR path
ls -la $(poetry run python -c "from simiir_api.config import settings; print(settings.simiir_repo_path)")

# Test database connection
poetry run python -c "
import asyncio
from simiir_api.database import get_session
async def test():
    async for session in get_session():
        print('Database connection OK')
        break
asyncio.run(test())
"
```

## Tips

- Use `jq` for pretty JSON output: `curl ... | jq`
- Use `watch` to monitor status: `watch -n 2 'curl -s ... | jq'`
- Save simulation IDs in variables for easy access
- Use `.env` file for configuration instead of command line
- Check Swagger UI for interactive testing
- View logs in real-time with `tail -f`

