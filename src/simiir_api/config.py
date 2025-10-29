"""Configuration settings for simIIR API"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_title: str = "SimIIR API"
    api_version: str = "0.1.0"
    api_description: str = "FastAPI wrapper for simIIR framework - Async simulation execution and management"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./simiir_api.db"
    
    # SimIIR Settings
    # Default: assumes simIIR is cloned at same level as simiir-api/
    simiir_repo_path: Path = Path("../simiir")
    simiir_python_path: Path = Path("../simiir")
    simiir_data_path: Path = Path("../simiir/example_data")
    
    # Simulation Settings
    max_concurrent_simulations: int = 3
    checkpoint_interval: int = 100  # Save checkpoint every N iterations
    output_base_path: Path = Path("./outputs")
    
    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("./logs/simiir_api.log")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

