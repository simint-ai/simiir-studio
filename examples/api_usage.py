"""
Example usage of the SimIIR API
"""

import requests
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


def create_simulation():
    """Create a new simulation"""
    
    # Load example config
    config_path = Path(__file__).parent / "example_simulation_config.xml"
    with open(config_path, "r") as f:
        config_content = f.read()
    
    # Create simulation
    response = requests.post(
        f"{BASE_URL}/simulations/",
        json={
            "name": "Test Simulation",
            "description": "Testing the API",
            "config_content": config_content,
            "users": ["user1", "user2"],
            "topics": ["303", "307"],
            "metadata": {
                "experiment": "query_prediction",
                "version": "1.0"
            }
        }
    )
    
    if response.status_code == 201:
        simulation = response.json()
        print(f"✓ Created simulation: {simulation['id']}")
        return simulation['id']
    else:
        print(f"✗ Failed to create simulation: {response.text}")
        return None


def start_simulation(sim_id):
    """Start a simulation"""
    
    response = requests.post(
        f"{BASE_URL}/simulations/{sim_id}/control",
        json={
            "action": "start"
        }
    )
    
    if response.status_code == 200:
        print(f"✓ Started simulation: {sim_id}")
        return True
    else:
        print(f"✗ Failed to start simulation: {response.text}")
        return False


def get_simulation_status(sim_id):
    """Get simulation status"""
    
    response = requests.get(f"{BASE_URL}/simulations/{sim_id}")
    
    if response.status_code == 200:
        simulation = response.json()
        status = simulation['status']
        progress = simulation['progress_percentage']
        print(f"Status: {status} ({progress}%)")
        return simulation
    else:
        print(f"✗ Failed to get simulation: {response.text}")
        return None


def pause_simulation(sim_id):
    """Pause a simulation"""
    
    response = requests.post(
        f"{BASE_URL}/simulations/{sim_id}/control",
        json={
            "action": "pause",
            "checkpoint_before_action": True
        }
    )
    
    if response.status_code == 200:
        print(f"✓ Paused simulation: {sim_id}")
        return True
    else:
        print(f"✗ Failed to pause simulation: {response.text}")
        return False


def resume_simulation(sim_id):
    """Resume a simulation"""
    
    response = requests.post(
        f"{BASE_URL}/simulations/{sim_id}/control",
        json={
            "action": "resume"
        }
    )
    
    if response.status_code == 200:
        print(f"✓ Resumed simulation: {sim_id}")
        return True
    else:
        print(f"✗ Failed to resume simulation: {response.text}")
        return False


def stop_simulation(sim_id):
    """Stop a simulation"""
    
    response = requests.post(
        f"{BASE_URL}/simulations/{sim_id}/control",
        json={
            "action": "stop"
        }
    )
    
    if response.status_code == 200:
        print(f"✓ Stopped simulation: {sim_id}")
        return True
    else:
        print(f"✗ Failed to stop simulation: {response.text}")
        return False


def get_results(sim_id):
    """Get simulation results"""
    
    response = requests.get(f"{BASE_URL}/simulations/{sim_id}/results")
    
    if response.status_code == 200:
        results = response.json()
        print(f"\n✓ Results for {sim_id}:")
        print(f"  Status: {results['status']}")
        print(f"  Queries: {len(results['queries'])}")
        print(f"  Output files: {len(results['output_files'])}")
        return results
    else:
        print(f"✗ Failed to get results: {response.text}")
        return None


def get_logs(sim_id, tail=50):
    """Get simulation logs"""
    
    response = requests.get(
        f"{BASE_URL}/simulations/{sim_id}/logs",
        params={"tail": tail}
    )
    
    if response.status_code == 200:
        log_data = response.json()
        print(f"\n✓ Logs for {sim_id} (last {tail} lines):")
        print(log_data['logs'])
        return log_data
    else:
        print(f"✗ Failed to get logs: {response.text}")
        return None


def list_simulations():
    """List all simulations"""
    
    response = requests.get(f"{BASE_URL}/simulations/")
    
    if response.status_code == 200:
        simulations = response.json()
        print(f"\n✓ Found {len(simulations)} simulations:")
        for sim in simulations:
            print(f"  - {sim['id']}: {sim['name']} ({sim['status']})")
        return simulations
    else:
        print(f"✗ Failed to list simulations: {response.text}")
        return None


def main():
    """Main example workflow"""
    
    print("SimIIR API Example Usage\n" + "=" * 50)
    
    # 1. Create a simulation
    print("\n1. Creating simulation...")
    sim_id = create_simulation()
    if not sim_id:
        return
    
    # 2. Start the simulation
    print("\n2. Starting simulation...")
    if not start_simulation(sim_id):
        return
    
    # 3. Monitor progress
    print("\n3. Monitoring progress...")
    for i in range(5):
        time.sleep(2)
        get_simulation_status(sim_id)
    
    # 4. Pause simulation
    print("\n4. Pausing simulation...")
    pause_simulation(sim_id)
    time.sleep(1)
    
    # 5. Resume simulation
    print("\n5. Resuming simulation...")
    resume_simulation(sim_id)
    time.sleep(2)
    
    # 6. Get logs
    print("\n6. Getting logs...")
    get_logs(sim_id, tail=20)
    
    # 7. List all simulations
    print("\n7. Listing all simulations...")
    list_simulations()
    
    # 8. Wait for completion or stop
    print("\n8. Waiting for completion (or stopping after 10 seconds)...")
    for i in range(5):
        time.sleep(2)
        sim = get_simulation_status(sim_id)
        if sim and sim['status'] in ['completed', 'failed']:
            break
    else:
        # Stop if not completed
        print("\nStopping simulation...")
        stop_simulation(sim_id)
    
    # 9. Get final results
    print("\n9. Getting final results...")
    get_results(sim_id)
    
    print("\n" + "=" * 50)
    print("Example complete!")


if __name__ == "__main__":
    main()

