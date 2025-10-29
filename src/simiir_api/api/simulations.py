"""Simulation API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.simulation import SimulationStatus
from ..schemas import (
    SimulationCreate,
    SimulationUpdate,
    SimulationResponse,
    SimulationExecutionControl,
    SimulationResultsResponse,
    SimulationLogsResponse,
    SimulationCheckpointResponse,
)
from ..services.simulation_manager import simulation_manager

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    simulation: SimulationCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new simulation configuration.
    
    The simulation will be created in PENDING state and can be started later.
    """
    try:
        sim = await simulation_manager.create_simulation(
            session=session,
            name=simulation.name,
            config_content=simulation.config_content,
            description=simulation.description,
            users=simulation.users,
            topics=simulation.topics,
            metadata=simulation.metadata,
        )
        return sim
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[SimulationResponse])
async def list_simulations(
    status: Optional[SimulationStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all simulations with optional filtering.
    """
    simulations = await simulation_manager.list_simulations(
        session=session,
        status=status,
        limit=limit,
        offset=offset,
    )
    return simulations


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get details of a specific simulation.
    """
    simulation = await simulation_manager.get_simulation(session, simulation_id)
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulation


@router.patch("/{simulation_id}", response_model=SimulationResponse)
async def update_simulation(
    simulation_id: str,
    update_data: SimulationUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update simulation configuration (only allowed for PENDING simulations).
    """
    simulation = await simulation_manager.get_simulation(session, simulation_id)
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if simulation.status != SimulationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Can only update simulations in PENDING state"
        )
    
    # Update fields
    if update_data.name:
        simulation.name = update_data.name
    if update_data.description is not None:
        simulation.description = update_data.description
    if update_data.config_content:
        simulation.config_content = update_data.config_content
        # Re-write config file
        with open(simulation.config_file_path, "w") as f:
            f.write(update_data.config_content)
    if update_data.metadata:
        simulation.simulation_metadata = update_data.metadata
    
    await session.commit()
    await session.refresh(simulation)
    
    return simulation


@router.post("/{simulation_id}/control", response_model=SimulationResponse)
async def control_simulation(
    simulation_id: str,
    control: SimulationExecutionControl,
    session: AsyncSession = Depends(get_session),
):
    """
    Control simulation execution: start, pause, resume, stop.
    
    - **start**: Start a PENDING simulation
    - **pause**: Pause a RUNNING simulation
    - **resume**: Resume a PAUSED simulation
    - **stop**: Stop a RUNNING or PAUSED simulation
    """
    action = control.action.lower()
    
    try:
        if action == "start":
            simulation = await simulation_manager.start_simulation(session, simulation_id)
        elif action == "pause":
            simulation = await simulation_manager.pause_simulation(
                session, simulation_id, control.checkpoint_before_action
            )
        elif action == "resume":
            simulation = await simulation_manager.resume_simulation(session, simulation_id)
        elif action == "stop":
            simulation = await simulation_manager.stop_simulation(session, simulation_id)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {action}. Must be one of: start, pause, resume, stop"
            )
        
        return simulation
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/results", response_model=SimulationResultsResponse)
async def get_simulation_results(
    simulation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get simulation results including queries, interactions, and metrics.
    """
    try:
        results = await simulation_manager.get_results(session, simulation_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/logs", response_model=SimulationLogsResponse)
async def get_simulation_logs(
    simulation_id: str,
    tail: Optional[int] = Query(None, description="Return only last N lines"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get simulation logs.
    """
    try:
        simulation = await simulation_manager.get_simulation(session, simulation_id)
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        logs = await simulation_manager.get_logs(session, simulation_id, tail)
        
        return SimulationLogsResponse(
            simulation_id=simulation.id,
            logs=logs,
            log_file_path=simulation.log_file_path,
            last_updated=simulation.updated_at,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/checkpoints", response_model=List[SimulationCheckpointResponse])
async def list_checkpoints(
    simulation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    List all checkpoints for a simulation.
    """
    simulation = await simulation_manager.get_simulation(session, simulation_id)
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulation.checkpoints


@router.delete("/{simulation_id}", status_code=204)
async def delete_simulation(
    simulation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a simulation (only PENDING, COMPLETED, FAILED, or CANCELLED).
    """
    simulation = await simulation_manager.get_simulation(session, simulation_id)
    
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if simulation.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running or paused simulation. Stop it first."
        )
    
    # Delete from database
    await session.delete(simulation)
    await session.commit()
    
    return None

