# SimIIR API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. This can be added using FastAPI security features.

---

## Endpoints

### 1. Root
Get API information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "simIIR API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

---

### 2. Health Check
Check API health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Simulations Management

### 3. Create Simulation
Create a new simulation configuration.

**Endpoint:** `POST /simulations/`

**Request Body:**
```json
{
  "name": "My Simulation",
  "description": "Optional description",
  "config_content": "<?xml version='1.0' encoding='UTF-8'?>...",
  "users": ["user1", "user2"],  // Optional: override users
  "topics": ["303", "307"],      // Optional: override topics
  "metadata": {                  // Optional: additional metadata
    "experiment_type": "query_prediction"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "sim_abc123def456",
  "name": "My Simulation",
  "description": "Optional description",
  "status": "pending",
  "config_file_path": "/path/to/config.xml",
  "process_id": null,
  "current_iteration": 0,
  "total_iterations": null,
  "progress_percentage": 0,
  "output_directory": "/path/to/output",
  "log_file_path": "/path/to/simulation.log",
  "results_file_path": "/path/to/results.json",
  "metadata": {},
  "error_message": null,
  "created_at": "2025-10-28T10:00:00",
  "started_at": null,
  "completed_at": null,
  "updated_at": "2025-10-28T10:00:00"
}
```

---

### 4. List Simulations
List all simulations with optional filtering.

**Endpoint:** `GET /simulations/`

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `running`, `paused`, `completed`, `failed`, `cancelled`)
- `limit` (optional, default: 100): Maximum number of results (1-1000)
- `offset` (optional, default: 0): Offset for pagination

**Examples:**
```
GET /simulations/
GET /simulations/?status=running
GET /simulations/?limit=50&offset=100
GET /simulations/?status=completed&limit=20
```

**Response:** `200 OK`
```json
[
  {
    "id": "sim_abc123",
    "name": "Simulation 1",
    "status": "running",
    ...
  },
  {
    "id": "sim_def456",
    "name": "Simulation 2",
    "status": "completed",
    ...
  }
]
```

---

### 5. Get Simulation
Get details of a specific simulation.

**Endpoint:** `GET /simulations/{simulation_id}`

**Response:** `200 OK`
```json
{
  "id": "sim_abc123",
  "name": "My Simulation",
  "status": "running",
  "progress_percentage": 45,
  ...
}
```

**Error:** `404 Not Found` if simulation doesn't exist

---

### 6. Update Simulation
Update simulation configuration (only allowed for PENDING simulations).

**Endpoint:** `PATCH /simulations/{simulation_id}`

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "config_content": "<?xml...>",
  "metadata": {}
}
```

**Response:** `200 OK`

**Error:** `400 Bad Request` if simulation is not in PENDING state

---

### 7. Delete Simulation
Delete a simulation (only PENDING, COMPLETED, FAILED, or CANCELLED).

**Endpoint:** `DELETE /simulations/{simulation_id}`

**Response:** `204 No Content`

**Error:** `400 Bad Request` if simulation is RUNNING or PAUSED

---

## Execution Control

### 8. Control Simulation Execution
Control simulation execution with start, pause, resume, or stop actions.

**Endpoint:** `POST /simulations/{simulation_id}/control`

**Request Body:**
```json
{
  "action": "start",  // or "pause", "resume", "stop"
  "checkpoint_before_action": false  // optional, for pause action
}
```

#### Actions:

**START** - Start a pending simulation
```json
{
  "action": "start"
}
```
- Allowed states: `pending`
- New state: `running`

**PAUSE** - Pause a running simulation
```json
{
  "action": "pause",
  "checkpoint_before_action": true
}
```
- Allowed states: `running`
- New state: `paused`
- Creates checkpoint if `checkpoint_before_action` is `true`

**RESUME** - Resume a paused simulation
```json
{
  "action": "resume"
}
```
- Allowed states: `paused`
- New state: `running`

**STOP** - Stop a running or paused simulation
```json
{
  "action": "stop"
}
```
- Allowed states: `running`, `paused`
- New state: `cancelled`
- Terminates the simulation process

**Response:** `200 OK`
```json
{
  "id": "sim_abc123",
  "status": "running",
  ...
}
```

**Errors:**
- `400 Bad Request` - Invalid action or state
- `404 Not Found` - Simulation not found

---

## Results and Monitoring

### 9. Get Simulation Results
Get simulation results including queries, interactions, and metrics.

**Endpoint:** `GET /simulations/{simulation_id}/results`

**Response:** `200 OK`
```json
{
  "simulation_id": "sim_abc123",
  "status": "completed",
  "queries": [
    {
      "query": "information retrieval",
      "session_id": "s1",
      "rank": 1
    }
  ],
  "interactions": [
    {
      "session_id": "s1",
      "action": "query",
      "timestamp": "2025-10-28T10:05:00"
    }
  ],
  "metrics": {
    "total_queries": 100,
    "avg_query_length": 3.5,
    "total_clicks": 45
  },
  "output_files": [
    "simulation.log",
    "queries.txt",
    "results.json"
  ]
}
```

---

### 10. Get Simulation Logs
Get simulation logs with optional tail limit.

**Endpoint:** `GET /simulations/{simulation_id}/logs`

**Query Parameters:**
- `tail` (optional): Return only last N lines

**Examples:**
```
GET /simulations/sim_abc123/logs
GET /simulations/sim_abc123/logs?tail=100
```

**Response:** `200 OK`
```json
{
  "simulation_id": "sim_abc123",
  "logs": "2025-10-28 10:00:00 - Starting simulation...\n...",
  "log_file_path": "/path/to/simulation.log",
  "last_updated": "2025-10-28T10:30:00"
}
```

---

### 11. List Checkpoints
List all checkpoints for a simulation.

**Endpoint:** `GET /simulations/{simulation_id}/checkpoints`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "simulation_id": "sim_abc123",
    "checkpoint_iteration": 100,
    "checkpoint_file_path": "/path/to/checkpoint_100.json",
    "created_at": "2025-10-28T10:15:00"
  },
  {
    "id": 2,
    "simulation_id": "sim_abc123",
    "checkpoint_iteration": 200,
    "checkpoint_file_path": "/path/to/checkpoint_200.json",
    "created_at": "2025-10-28T10:20:00"
  }
]
```

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request or validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Simulation Status Values

- `pending` - Simulation created, not yet started
- `running` - Simulation is currently executing
- `paused` - Simulation is paused
- `completed` - Simulation completed successfully
- `failed` - Simulation failed with error
- `cancelled` - Simulation was stopped by user

---

## Error Response Format

All errors return a standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Example Workflow

1. **Create a simulation:**
```bash
curl -X POST http://localhost:8000/simulations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Sim",
    "config_content": "<?xml...>",
    "users": ["user1"],
    "topics": ["303"]
  }'
```

2. **Start the simulation:**
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'
```

3. **Check status:**
```bash
curl http://localhost:8000/simulations/sim_abc123
```

4. **Pause if needed:**
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause", "checkpoint_before_action": true}'
```

5. **Resume:**
```bash
curl -X POST http://localhost:8000/simulations/sim_abc123/control \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}'
```

6. **Get logs:**
```bash
curl http://localhost:8000/simulations/sim_abc123/logs?tail=50
```

7. **Get results:**
```bash
curl http://localhost:8000/simulations/sim_abc123/results
```

---

## Interactive Documentation

For interactive API documentation, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

