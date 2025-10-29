"""Simulation manager for async execution with pause/resume/checkpoint support"""

import asyncio
import os
import signal
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.simulation import Simulation, SimulationStatus, SimulationCheckpoint
from ..config import settings
from ..utils.xml_config_manager import XMLConfigManager

logger = logging.getLogger(__name__)


class SimulationManager:
    """Manages simulation lifecycle: creation, execution, monitoring, and control"""
    
    def __init__(self):
        self.running_simulations: Dict[str, subprocess.Popen] = {}
        self.simulation_tasks: Dict[str, asyncio.Task] = {}
        
    async def create_simulation(
        self,
        session: AsyncSession,
        name: str,
        config_content: str,
        description: Optional[str] = None,
        users: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Simulation:
        """Create a new simulation"""
        
        # Generate unique ID
        sim_id = f"sim_{uuid4().hex[:12]}"
        
        # Create output directory
        output_dir = settings.output_base_path / sim_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save configuration file
        config_file_path = output_dir / "config.xml"
        
        # Process XML config with user/topic overrides
        xml_manager = XMLConfigManager(config_content)
        if users:
            xml_manager.set_users(users)
        if topics:
            xml_manager.set_topics(topics)
        
        # Update output paths in XML (use absolute path)
        xml_manager.set_output_directory(str(output_dir.resolve()))
        
        processed_config = xml_manager.to_string()
        
        # Write config file
        with open(config_file_path, "w") as f:
            f.write(processed_config)
        
        # Create simulation record
        simulation = Simulation(
            id=sim_id,
            name=name,
            description=description,
            config_file_path=str(config_file_path),
            config_content=processed_config,
            status=SimulationStatus.PENDING,
            output_directory=str(output_dir),
            log_file_path=str(output_dir / "simulation.log"),
            results_file_path=str(output_dir / "results.json"),
            simulation_metadata=metadata or {},
        )
        
        session.add(simulation)
        await session.commit()
        await session.refresh(simulation)
        
        logger.info(f"Created simulation {sim_id}: {name}")
        return simulation
    
    async def start_simulation(
        self,
        session: AsyncSession,
        simulation_id: str,
    ) -> Simulation:
        """Start a simulation"""
        
        # Get simulation
        result = await session.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        if simulation.status == SimulationStatus.RUNNING:
            raise ValueError(f"Simulation {simulation_id} is already running")
        
        # Update status
        simulation.status = SimulationStatus.RUNNING
        simulation.started_at = datetime.utcnow()
        await session.commit()
        
        # Refresh to detach from session
        await session.refresh(simulation)
        
        # Start simulation process (pass simulation_id, not the session or object)
        task = asyncio.create_task(
            self._run_simulation_process(simulation_id)
        )
        self.simulation_tasks[simulation_id] = task
        
        logger.info(f"Started simulation {simulation_id}")
        return simulation
    
    async def _run_simulation_process(
        self,
        simulation_id: str,
    ):
        """Run the simulation as a subprocess"""
        
        # Import here to avoid circular dependency
        from ..database import async_session_maker
        
        # Create a new session for this task
        async with async_session_maker() as session:
            try:
                # Get the simulation
                result = await session.execute(
                    select(Simulation).where(Simulation.id == simulation_id)
                )
                simulation = result.scalar_one_or_none()
                
                if not simulation:
                    logger.error(f"Simulation {simulation_id} not found")
                    return
                
                # Prepare environment
                env = os.environ.copy()
                env["PYTHONPATH"] = str(settings.simiir_python_path)
                
                # Prepare command
                run_script = settings.simiir_repo_path / "simiir" / "run_simiir.py"
                
                # Make config file path absolute
                from pathlib import Path
                config_file = Path(simulation.config_file_path).resolve()
                
                # Determine working directory and command
                # Check if simIIR has its own pyproject.toml (poetry setup)
                simiir_pyproject = settings.simiir_repo_path / "pyproject.toml"
                
                if simiir_pyproject.exists():
                    # SimIIR has its own poetry environment
                    work_dir = settings.simiir_repo_path
                    cmd = [
                        "poetry",
                        "run",
                        "python",
                        str(run_script),
                        str(config_file),
                    ]
                    logger.info(f"Using simIIR's own poetry environment at {work_dir}")
                else:
                    # Use backend's poetry environment (fallback for owlergpt setup)
                    backend_dir = settings.simiir_repo_path.parent / "backend"
                    if backend_dir.exists():
                        work_dir = backend_dir
                        cmd = [
                            "poetry",
                            "run",
                            "python",
                            str(run_script),
                            str(config_file),
                        ]
                        logger.info(f"Using backend poetry environment at {work_dir}")
                    else:
                        # No poetry, use system python
                        work_dir = settings.simiir_repo_path
                        cmd = [
                            "python",
                            str(run_script),
                            str(config_file),
                        ]
                        logger.info(f"Using system python at {work_dir}")
                
                logger.info(f"Running command: {' '.join(cmd)}")
                
                # Start process
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(work_dir),
                    preexec_fn=os.setsid if os.name != 'nt' else None,
                )
                
                # Store process
                self.running_simulations[simulation.id] = process
                simulation.process_id = str(process.pid)
                await session.commit()
                
                # Monitor process
                await self._monitor_simulation(session, simulation, process)
                
            except Exception as e:
                logger.error(f"Error running simulation {simulation_id}: {e}")
                # Try to update status
                try:
                    result = await session.execute(
                        select(Simulation).where(Simulation.id == simulation_id)
                    )
                    simulation = result.scalar_one_or_none()
                    if simulation:
                        simulation.status = SimulationStatus.FAILED
                        simulation.error_message = str(e)
                        await session.commit()
                except:
                    pass
    
    async def _monitor_simulation(
        self,
        session: AsyncSession,
        simulation: Simulation,
        process: subprocess.Popen,
    ):
        """Monitor simulation progress"""
        
        log_file = open(simulation.log_file_path, "w")
        
        try:
            # Monitor stdout/stderr
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                # Read output
                line = process.stdout.readline()
                if line:
                    log_file.write(line.decode())
                    log_file.flush()
                
                # Update progress (parse from logs if available)
                await self._update_progress(session, simulation)
                
                # Check for checkpoint interval
                if simulation.current_iteration % settings.checkpoint_interval == 0:
                    await self._create_checkpoint(session, simulation)
                
                await asyncio.sleep(0.1)
            
            # Process completed
            return_code = process.wait()
            
            if return_code == 0:
                simulation.status = SimulationStatus.COMPLETED
                simulation.completed_at = datetime.utcnow()
                logger.info(f"Simulation {simulation.id} completed successfully")
            else:
                simulation.status = SimulationStatus.FAILED
                stderr = process.stderr.read().decode()
                simulation.error_message = stderr
                logger.error(f"Simulation {simulation.id} failed: {stderr}")
            
        except Exception as e:
            logger.error(f"Error monitoring simulation {simulation.id}: {e}")
            simulation.status = SimulationStatus.FAILED
            simulation.error_message = str(e)
        
        finally:
            log_file.close()
            await session.commit()
            
            # Cleanup
            if simulation.id in self.running_simulations:
                del self.running_simulations[simulation.id]
    
    async def _update_progress(
        self,
        session: AsyncSession,
        simulation: Simulation,
    ):
        """Update simulation progress by parsing logs"""
        
        # This is a simple implementation - can be enhanced to parse actual progress
        # from the simulation logs
        
        try:
            if os.path.exists(simulation.log_file_path):
                with open(simulation.log_file_path, "r") as f:
                    lines = f.readlines()
                    # Simple heuristic: count completed actions
                    simulation.current_iteration = len(lines)
                    
                    # Update percentage if total is known
                    if simulation.total_iterations:
                        simulation.progress_percentage = min(
                            100,
                            int((simulation.current_iteration / simulation.total_iterations) * 100)
                        )
                
                await session.commit()
        except Exception as e:
            logger.warning(f"Could not update progress for {simulation.id}: {e}")
    
    async def pause_simulation(
        self,
        session: AsyncSession,
        simulation_id: str,
        create_checkpoint: bool = True,
    ) -> Simulation:
        """Pause a running simulation"""
        
        result = await session.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        if simulation.status != SimulationStatus.RUNNING:
            raise ValueError(f"Simulation {simulation_id} is not running")
        
        # Create checkpoint before pausing
        if create_checkpoint:
            await self._create_checkpoint(session, simulation)
        
        # Send pause signal (SIGSTOP on Unix)
        if simulation_id in self.running_simulations:
            process = self.running_simulations[simulation_id]
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGSTOP)
            else:
                # On Windows, we need to use different approach
                # For now, just update status - full pause support needs Windows-specific implementation
                pass
        
        simulation.status = SimulationStatus.PAUSED
        await session.commit()
        
        logger.info(f"Paused simulation {simulation_id}")
        return simulation
    
    async def resume_simulation(
        self,
        session: AsyncSession,
        simulation_id: str,
    ) -> Simulation:
        """Resume a paused simulation"""
        
        result = await session.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        if simulation.status != SimulationStatus.PAUSED:
            raise ValueError(f"Simulation {simulation_id} is not paused")
        
        # Send resume signal (SIGCONT on Unix)
        if simulation_id in self.running_simulations:
            process = self.running_simulations[simulation_id]
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGCONT)
        
        simulation.status = SimulationStatus.RUNNING
        await session.commit()
        
        logger.info(f"Resumed simulation {simulation_id}")
        return simulation
    
    async def stop_simulation(
        self,
        session: AsyncSession,
        simulation_id: str,
    ) -> Simulation:
        """Stop a simulation"""
        
        result = await session.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        simulation = result.scalar_one_or_none()
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        if simulation.status not in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
            raise ValueError(f"Simulation {simulation_id} is not running or paused")
        
        # Terminate process
        if simulation_id in self.running_simulations:
            process = self.running_simulations[simulation_id]
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if doesn't terminate
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            
            del self.running_simulations[simulation_id]
        
        # Cancel task
        if simulation_id in self.simulation_tasks:
            task = self.simulation_tasks[simulation_id]
            task.cancel()
            del self.simulation_tasks[simulation_id]
        
        simulation.status = SimulationStatus.CANCELLED
        simulation.completed_at = datetime.utcnow()
        await session.commit()
        
        logger.info(f"Stopped simulation {simulation_id}")
        return simulation
    
    async def _create_checkpoint(
        self,
        session: AsyncSession,
        simulation: Simulation,
    ) -> SimulationCheckpoint:
        """Create a checkpoint for the simulation"""
        
        checkpoint_data = {
            "iteration": simulation.current_iteration,
            "timestamp": datetime.utcnow().isoformat(),
            "status": simulation.status.value,
        }
        
        # Save checkpoint file
        checkpoint_dir = Path(simulation.output_directory) / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f"checkpoint_{simulation.current_iteration}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # Create checkpoint record
        checkpoint = SimulationCheckpoint(
            simulation_id=simulation.id,
            checkpoint_iteration=simulation.current_iteration,
            checkpoint_data=checkpoint_data,
            checkpoint_file_path=str(checkpoint_file),
        )
        
        session.add(checkpoint)
        await session.commit()
        
        logger.info(f"Created checkpoint for simulation {simulation.id} at iteration {simulation.current_iteration}")
        return checkpoint
    
    async def get_simulation(
        self,
        session: AsyncSession,
        simulation_id: str,
    ) -> Optional[Simulation]:
        """Get simulation by ID"""
        
        result = await session.execute(
            select(Simulation).where(Simulation.id == simulation_id)
        )
        return result.scalar_one_or_none()
    
    async def list_simulations(
        self,
        session: AsyncSession,
        status: Optional[SimulationStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Simulation]:
        """List simulations with optional filtering"""
        
        query = select(Simulation)
        
        if status:
            query = query.where(Simulation.status == status)
        
        query = query.order_by(Simulation.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_results(
        self,
        session: AsyncSession,
        simulation_id: str,
    ) -> Dict[str, Any]:
        """Get simulation results"""
        
        simulation = await self.get_simulation(session, simulation_id)
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        results = {
            "simulation_id": simulation.id,
            "status": simulation.status,
            "queries": [],
            "interactions": [],
            "metrics": {},
            "output_files": [],
        }
        
        # Parse output directory for result files
        output_dir = Path(simulation.output_directory)
        
        if output_dir.exists():
            # List output files
            results["output_files"] = [
                str(f.relative_to(output_dir))
                for f in output_dir.rglob("*")
                if f.is_file()
            ]
            
            # Parse queries file if exists
            queries_file = output_dir / "queries.txt"
            if queries_file.exists():
                with open(queries_file, "r") as f:
                    results["queries"] = [
                        {"query": line.strip()}
                        for line in f.readlines()
                        if line.strip()
                    ]
            
            # Parse results JSON if exists
            results_json = output_dir / "results.json"
            if results_json.exists():
                with open(results_json, "r") as f:
                    data = json.load(f)
                    results.update(data)
        
        return results
    
    async def get_logs(
        self,
        session: AsyncSession,
        simulation_id: str,
        tail_lines: Optional[int] = None,
    ) -> str:
        """Get simulation logs"""
        
        simulation = await self.get_simulation(session, simulation_id)
        
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        if not simulation.log_file_path or not os.path.exists(simulation.log_file_path):
            return ""
        
        with open(simulation.log_file_path, "r") as f:
            if tail_lines:
                lines = f.readlines()
                return "".join(lines[-tail_lines:])
            else:
                return f.read()


# Global simulation manager instance
simulation_manager = SimulationManager()

