# SimIIR API Architecture

## Overview

The SimIIR API is a FastAPI-based wrapper that provides RESTful endpoints for managing simIIR simulations with async execution, pause/resume capabilities, checkpointing, and comprehensive monitoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│  (HTTP Requests, Python SDK, cURL, Web Frontend, etc.)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP/REST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              API Endpoints (Routers)                   │  │
│  │  - POST   /simulations/                               │  │
│  │  - GET    /simulations/                               │  │
│  │  - GET    /simulations/{id}                           │  │
│  │  - PATCH  /simulations/{id}                           │  │
│  │  - DELETE /simulations/{id}                           │  │
│  │  - POST   /simulations/{id}/control                   │  │
│  │  - GET    /simulations/{id}/results                   │  │
│  │  - GET    /simulations/{id}/logs                      │  │
│  │  - GET    /simulations/{id}/checkpoints               │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│  ┌───────────────────▼───────────────────────────────────┐  │
│  │            Pydantic Schemas (Validation)              │  │
│  │  - SimulationCreate, SimulationResponse              │  │
│  │  - SimulationExecutionControl                         │  │
│  │  - SimulationResultsResponse, etc.                    │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│  ┌───────────────────▼───────────────────────────────────┐  │
│  │             Service Layer (Business Logic)            │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │        SimulationManager                         │  │  │
│  │  │  - create_simulation()                          │  │  │
│  │  │  - start_simulation()                           │  │  │
│  │  │  - pause_simulation()                           │  │  │
│  │  │  - resume_simulation()                          │  │  │
│  │  │  - stop_simulation()                            │  │  │
│  │  │  - get_results()                                │  │  │
│  │  │  - get_logs()                                   │  │  │
│  │  │  - _create_checkpoint()                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│  ┌───────────────────▼───────────────────────────────────┐  │
│  │           Utilities & Helpers                         │  │
│  │  - XMLConfigManager (XML processing)                 │  │
│  │  - Configuration management                           │  │
│  └───────────────────┬───────────────────────────────────┘  │
└────────────────────┬─┴───────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────────┐   ┌──────────────────────────┐
│   SQLAlchemy DB   │   │   Process Management     │
│  (SQLite/Async)   │   │                          │
│                   │   │  ┌────────────────────┐  │
│  - Simulations    │   │  │  asyncio.Task      │  │
│  - Checkpoints    │   │  │  subprocess.Popen  │  │
│  - Status         │   │  └────────────────────┘  │
└────────┬──────────┘   └──────────┬───────────────┘
         │                         │
         │                         ▼
         │              ┌─────────────────────┐
         │              │   simIIR Framework  │
         │              │   (run_simiir.py)   │
         │              └─────────┬───────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────────┐
│           File System                        │
│  - XML Configs                              │
│  - Output Files (queries, logs, etc.)       │
│  - Checkpoints                              │
└─────────────────────────────────────────────┘
```

## Components

### 1. API Layer (`api/`)
- **Routers**: Define API endpoints and handle HTTP requests
- **Dependency Injection**: Use FastAPI's dependency system for database sessions
- **Error Handling**: Convert exceptions to appropriate HTTP responses

### 2. Schema Layer (`schemas/`)
- **Request Validation**: Pydantic models validate incoming requests
- **Response Serialization**: Ensure consistent response formats
- **Type Safety**: Provide type hints for better IDE support

### 3. Service Layer (`services/`)
- **SimulationManager**: Core business logic for simulation management
  - Lifecycle management (create, start, pause, resume, stop)
  - Process execution and monitoring
  - Checkpoint creation and recovery
  - Result aggregation

### 4. Model Layer (`models/`)
- **Database Models**: SQLAlchemy ORM models
  - `Simulation`: Main simulation records
  - `SimulationCheckpoint`: Checkpoint data for pause/resume
  - Status tracking and metadata

### 5. Utilities (`utils/`)
- **XMLConfigManager**: Parse and modify simIIR XML configurations
- **Configuration**: Application settings and environment variables

### 6. Database Layer (`database.py`)
- **Async Engine**: SQLAlchemy async engine for non-blocking DB operations
- **Session Management**: Dependency injection for database sessions
- **Connection Pooling**: Efficient connection management

## Data Flow

### Creating and Running a Simulation

```
1. Client Request
   └─> POST /simulations/ with config XML

2. API Endpoint (simulations.py)
   └─> Validate request with SimulationCreate schema

3. SimulationManager.create_simulation()
   ├─> Parse XML with XMLConfigManager
   ├─> Apply user/topic overrides
   ├─> Create output directory
   ├─> Save processed XML config
   └─> Create Simulation record in DB

4. Client Request
   └─> POST /simulations/{id}/control {"action": "start"}

5. SimulationManager.start_simulation()
   ├─> Update status to RUNNING
   ├─> Create asyncio.Task
   └─> Start subprocess (run_simiir.py)

6. SimulationManager._run_simulation_process()
   ├─> Execute simIIR with subprocess.Popen
   ├─> Monitor stdout/stderr
   ├─> Update progress periodically
   ├─> Create checkpoints at intervals
   └─> Update final status (COMPLETED/FAILED)

7. Client Request
   └─> GET /simulations/{id}/results

8. SimulationManager.get_results()
   ├─> Read output files
   ├─> Parse queries, logs, metrics
   └─> Return aggregated results
```

### Pause and Resume Flow

```
1. Pause Request
   └─> POST /simulations/{id}/control {"action": "pause", "checkpoint_before_action": true}

2. SimulationManager.pause_simulation()
   ├─> Create checkpoint (if requested)
   │   ├─> Capture current state
   │   ├─> Save checkpoint file
   │   └─> Create SimulationCheckpoint record
   ├─> Send SIGSTOP to process (Unix)
   └─> Update status to PAUSED

3. Resume Request
   └─> POST /simulations/{id}/control {"action": "resume"}

4. SimulationManager.resume_simulation()
   ├─> Send SIGCONT to process (Unix)
   └─> Update status to RUNNING
```

## Key Design Decisions

### 1. Async Architecture
- **Why**: Non-blocking I/O for better scalability
- **Implementation**: 
  - FastAPI with async endpoints
  - SQLAlchemy with async engine
  - asyncio for process management

### 2. Subprocess Execution
- **Why**: Isolation and process control
- **Implementation**:
  - subprocess.Popen for fine-grained control
  - Process groups (Unix) for signal management
  - stdout/stderr streaming for real-time logs

### 3. Checkpoint System
- **Why**: Support pause/resume and recovery
- **Implementation**:
  - Periodic checkpoint creation
  - JSON snapshot of current state
  - Database records for checkpoint metadata

### 4. File-Based Results
- **Why**: Preserve compatibility with simIIR
- **Implementation**:
  - Output directory per simulation
  - Parse standard simIIR output files
  - Aggregate results via API

### 5. SQLite with Async
- **Why**: Simple deployment, good for local use
- **Future**: Can switch to PostgreSQL for production
- **Implementation**: aiosqlite for async SQLite

## Scalability Considerations

### Current Limitations
- **Concurrent Simulations**: Configurable limit (default: 3)
- **Database**: SQLite (single file)
- **Process Management**: Local subprocess execution

### Future Enhancements
1. **Distributed Execution**:
   - Use Celery/RabbitMQ for task queue
   - Support remote workers
   - Scale horizontally

2. **Database**:
   - PostgreSQL for production
   - Connection pooling
   - Read replicas

3. **Storage**:
   - Object storage (S3) for outputs
   - Compression for large results
   - Cleanup policies

4. **Monitoring**:
   - Prometheus metrics
   - Health checks
   - Performance tracking

## Security Considerations

### Current State
- No authentication/authorization
- Local file system access
- Subprocess execution with current user

### Recommended Additions
1. **Authentication**:
   - API keys or OAuth2
   - FastAPI security utilities

2. **Authorization**:
   - User-based simulation access
   - Role-based permissions

3. **Input Validation**:
   - XML schema validation
   - Path sanitization
   - Resource limits

4. **Process Isolation**:
   - Containers for simulations
   - Resource quotas
   - Sandboxing

## Testing Strategy

### Unit Tests
- Service layer logic
- XML parsing and manipulation
- Schema validation

### Integration Tests
- API endpoints with test database
- Full simulation lifecycle
- Error handling

### E2E Tests
- Complete workflows
- Multiple concurrent simulations
- Pause/resume scenarios

## Deployment

### Local Development
```bash
poetry run simiir-api
```

### Docker
```bash
docker-compose up
```

### Production (Future)
- Kubernetes deployment
- Load balancer
- Database cluster
- Monitoring stack

## Configuration Management

### Environment Variables
All configuration via `.env` file:
- Server settings (host, port)
- Database connection
- simIIR paths
- Execution limits

### Runtime Configuration
- Via database models
- Per-simulation settings
- API-driven updates

## Monitoring and Logging

### Application Logs
- File-based logging (logs/simiir_api.log)
- Structured logging format
- Configurable log levels

### Simulation Logs
- Per-simulation log files
- Real-time streaming via API
- Tail support for recent logs

### Metrics (Future)
- Request counts
- Response times
- Active simulations
- Error rates

## Error Handling

### API Level
- HTTP status codes
- Consistent error format
- Detailed error messages

### Service Level
- Try-catch with logging
- Graceful degradation
- State recovery

### Process Level
- Return code checking
- stderr capture
- Cleanup on failure

