"""Database models for simulations"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class SimulationStatus(str, Enum):
    """Simulation status enum"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Simulation(Base):
    """Simulation model"""
    __tablename__ = "simulations"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    config_file_path = Column(String, nullable=False)
    config_content = Column(Text, nullable=False)  # XML content
    
    # Status
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING, nullable=False)
    
    # Execution details
    process_id = Column(String, nullable=True)
    current_iteration = Column(Integer, default=0)
    total_iterations = Column(Integer, nullable=True)
    progress_percentage = Column(Integer, default=0)
    
    # Output paths
    output_directory = Column(String, nullable=True)
    log_file_path = Column(String, nullable=True)
    results_file_path = Column(String, nullable=True)
    
    # Metadata
    simulation_metadata = Column(JSON, nullable=True)  # Additional configuration metadata
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    checkpoints = relationship("SimulationCheckpoint", back_populates="simulation", cascade="all, delete-orphan")


class SimulationCheckpoint(Base):
    """Simulation checkpoint model for pause/resume functionality"""
    __tablename__ = "simulation_checkpoints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String, ForeignKey("simulations.id"), nullable=False)
    
    checkpoint_iteration = Column(Integer, nullable=False)
    checkpoint_data = Column(JSON, nullable=False)  # State data for resume
    checkpoint_file_path = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="checkpoints")

