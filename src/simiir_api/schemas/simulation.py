"""Pydantic schemas for simulation requests and responses"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from ..models.simulation import SimulationStatus


class SimulationCreate(BaseModel):
    """Schema for creating a new simulation"""
    name: str = Field(..., description="Simulation name")
    description: Optional[str] = Field(None, description="Simulation description")
    config_content: str = Field(..., description="XML configuration content")
    
    # Optional overrides
    users: Optional[List[str]] = Field(None, description="List of user IDs to include")
    topics: Optional[List[str]] = Field(None, description="List of topic IDs to include")
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "My Simulation",
                "description": "Test simulation for query generation",
                "config_content": "<?xml version='1.0' encoding='UTF-8'?>...",
                "users": ["user1", "user2"],
                "topics": ["topic1", "topic2"],
                "metadata": {"experiment_type": "query_prediction"}
            }
        }
    )


class SimulationUpdate(BaseModel):
    """Schema for updating a simulation"""
    name: Optional[str] = None
    description: Optional[str] = None
    config_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class SimulationExecutionControl(BaseModel):
    """Schema for controlling simulation execution"""
    action: str = Field(..., description="Action: start, pause, resume, stop")
    checkpoint_before_action: bool = Field(False, description="Create checkpoint before action")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "pause",
                "checkpoint_before_action": True
            }
        }
    )


class SimulationResponse(BaseModel):
    """Schema for simulation response"""
    id: str
    name: str
    description: Optional[str] = None
    
    status: SimulationStatus
    
    config_file_path: str
    
    process_id: Optional[str] = None
    current_iteration: int = 0
    total_iterations: Optional[int] = None
    progress_percentage: int = 0
    
    output_directory: Optional[str] = None
    log_file_path: Optional[str] = None
    results_file_path: Optional[str] = None
    
    metadata: Optional[Dict[str, Any]] = Field(None, alias="simulation_metadata")
    error_message: Optional[str] = None
    
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SimulationCheckpointResponse(BaseModel):
    """Schema for checkpoint response"""
    id: int
    simulation_id: str
    checkpoint_iteration: int
    checkpoint_file_path: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SimulationResultsResponse(BaseModel):
    """Schema for simulation results"""
    simulation_id: str
    status: SimulationStatus
    
    # Results data
    queries: List[Dict[str, Any]] = Field(default_factory=list)
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # File paths
    output_files: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim123",
                "status": "completed",
                "queries": [
                    {"session_id": "s1", "query": "information retrieval", "rank": 1}
                ],
                "interactions": [
                    {"session_id": "s1", "action": "query", "timestamp": "2025-01-01T00:00:00"}
                ],
                "metrics": {
                    "total_queries": 100,
                    "avg_query_length": 3.5
                },
                "output_files": ["output.log", "queries.txt"]
            }
        }
    )


class SimulationLogsResponse(BaseModel):
    """Schema for simulation logs"""
    simulation_id: str
    logs: str
    log_file_path: Optional[str] = None
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)

