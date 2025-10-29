# SimIIR API - Quick Start Guide

Get started with the SimIIR API in 5 minutes!

## Prerequisites

- Python 3.9+
- Poetry (for dependency management)
- Git

## Installation

### Step 1: Clone SimIIR Framework

First, clone the simIIR framework at the root level (same level as simiir-api):

```bash
cd /simiir-studio  # Or your project root
git clone https://github.com/simint-ai/simiir-3.git simiir
```

Your directory structure should look like:
```
simiir-studio/
├── simiir/          ← SimIIR framework (just cloned)
└── simiir-api/      ← This API wrapper
```

### Step 2: Setup SimIIR Dependencies

SimIIR uses pip and requirements.txt:

```bash
cd simiir
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ../simiir-api
```

Note: The SimIIR API will automatically use the system Python to run simIIR since it doesn't have poetry.

### Step 3: Install SimIIR API

**Option A: Using the start script (Recommended)**

```bash
./start.sh
```

This will automatically:
1. Install poetry (if needed)
2. Install dependencies
3. Create directories
4. Set up environment
5. Initialize database
6. Start the server

**Option B: Manual setup**

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env

# Edit .env to set SIMIIR_REPO_PATH if not using default location
nano .env

# Create directories
mkdir -p outputs logs

# Start server
poetry run simiir-api
```

## First Simulation

### 1. Start the API
```bash
poetry run simiir-api
```

The API will be available at: http://localhost:8000

### 2. View API Documentation
Open your browser to: http://localhost:8000/docs

### 3. Create a Simulation

**Option A: Using the test script with real simIIR config (Recommended)**

```bash
poetry run python examples/test_with_real_config.py
```

This will:
- Read a real simIIR configuration from `../simiir/example_sims/trec_bm25_simulation.xml`
- Create a simulation via the API
- Show you commands to start and monitor it

**Option B: Using the Python example script**

```bash
poetry run python examples/api_usage.py
```

**Option C: Using curl**
```bash
# Read example config
CONFIG=$(cat examples/example_simulation_config.xml)

# Create simulation
curl -X POST http://localhost:8000/simulations/ \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"My First Simulation\",
    \"description\": \"Testing the API\",
    \"config_content\": \"$CONFIG\",
    \"users\": [\"user1\", \"user2\"],
    \"topics\": [\"303\", \"307\"]
  }"
```

Response:
```json
{
  "id": "sim_abc123def456",
  "name": "My First Simulation",
  "status": "pending",
  ...
}
```

### 4. Start the Simulation

```bash
# Replace sim_abc123 with your simulation ID
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

### 5. Monitor Progress

```bash
# Check status
curl http://localhost:8000/simulations/sim_abc123

# View logs (last 50 lines)
curl http://localhost:8000/simulations/sim_abc123/logs?tail=50
```

### 6. Get Results

```bash
# Once completed, get results
curl http://localhost:8000/simulations/sim_abc123/results
```

## Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Create simulation
response = requests.post(
    f"{BASE_URL}/simulations/",
    json={
        "name": "My Simulation",
        "config_content": open("examples/example_simulation_config.xml").read(),
        "users": ["user1", "user2"],
        "topics": ["303", "307"]
    }
)
sim_id = response.json()['id']

# Start simulation
requests.post(
    f"{BASE_URL}/simulations/{sim_id}/control",
    json={"action": "start"}
)

# Check status
status = requests.get(f"{BASE_URL}/simulations/{sim_id}").json()
print(f"Status: {status['status']}")

# Get results
results = requests.get(f"{BASE_URL}/simulations/{sim_id}/results").json()
print(f"Queries: {len(results['queries'])}")
```

## Common Operations

### List all simulations
```bash
curl http://localhost:8000/simulations/
```

### Filter by status
```bash
curl "http://localhost:8000/simulations/?status=running"
```

### Pause simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause", "checkpoint_before_action": true}'
```

### Resume simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}'
```

### Stop simulation
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "stop"}'
```

### List checkpoints
```bash
curl http://localhost:8000/simulations/sim_abc123/checkpoints
```

## Configuration

Edit `.env` file to configure:

```env
# Server settings
HOST=0.0.0.0
PORT=8000

# SimIIR paths
# Default expects simIIR at same level as simiir-api:
SIMIIR_REPO_PATH=../simiir
SIMIIR_DATA_PATH=../simiir/example_data

# Or use absolute paths:
# SIMIIR_REPO_PATH=/absolute/path/to/simiir
# SIMIIR_DATA_PATH=/absolute/path/to/simiir/example_data

# Simulation settings
MAX_CONCURRENT_SIMULATIONS=3
CHECKPOINT_INTERVAL=100
```

**Important**: If you cloned simIIR to a different location, update `SIMIIR_REPO_PATH` in `.env`

## Docker

### Build and run with Docker:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f
```

### Stop:
```bash
docker-compose down
```

## Quick Test with SimIIR Config

After starting the server, test with a simIIR configuration:

```bash
# Create simulation from simIIR example
poetry run python examples/test_with_real_config.py

# Output will show simulation ID, then:
# Start it
curl -X POST http://localhost:8000/simulations/{sim_id}/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# Monitor progress
curl http://localhost:8000/simulations/{sim_id}

# Watch logs in real-time
watch -n 2 "curl -s http://localhost:8000/simulations/{sim_id}/logs?tail=20"

# Get results when complete
curl http://localhost:8000/simulations/{sim_id}/results
```

## Troubleshooting

### SimIIR not cloned
```bash
cd ..  # Go to project root
git clone https://github.com/simint-ai/simiir-3.git simiir
cd simiir
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### Port already in use
Change the port in `.env`:
```env
PORT=8001
```

### SimIIR not found
Verify the path in `.env` matches where you cloned simIIR:
```bash
ls $SIMIIR_REPO_PATH/simiir/run_simiir.py
```

Update `.env` if needed:
```env
SIMIIR_REPO_PATH=/absolute/path/to/simiir
```

### Module not found errors
Make sure simIIR dependencies are installed:
```bash
cd ../simiir
source venv/bin/activate  # Activate the virtual environment
pip install -r requirements.txt
```

Or ensure the simIIR venv Python is in your PATH.

### Permission denied on start.sh
```bash
chmod +x start.sh
```

## Next Steps

1. **API Reference**: Check [API_REFERENCE.md](API_REFERENCE.md) for endpoint documentation
2. **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
3. **Commands**: Browse [COMMANDS.md](COMMANDS.md) for command cheat sheet
4. **Examples**: Explore examples in the `examples/` directory
5. **Interactive Docs**: Visit http://localhost:8000/docs for Swagger UI

## Support

For issues and questions:
1. Check the logs in `logs/simiir_api.log`
2. Review simulation logs in `outputs/{simulation_id}/simulation.log`
3. Refer to the main simIIR documentation

Happy simulating!

