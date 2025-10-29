#!/usr/bin/env python3
"""
Test the SimIIR API with a real simulation configuration from simIIR examples
"""

import json
import httpx
from pathlib import Path

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Read the real simIIR configuration
# Adjust this path if your simIIR is in a different location
config_file = Path("../../simiir/example_sims/trec_bm25_simulation.xml")

print(f"Reading configuration from: {config_file}")
with open(config_file, "r") as f:
    config_content = f.read()

print(f"Configuration size: {len(config_content)} bytes")

# Create simulation request
simulation_data = {
    "name": "CORE BM25 Sim4IA Simulation",
    "description": "Real simulation from simIIR examples - CORE dataset with BM25 and predetermined queries",
    "config_content": config_content,
    # Override with subset of topics for faster testing
    "topics": ["1", "2", "5"],
    "metadata": {
        "source": "trec_bm25_simulation.xml",
        "dataset": "CORE",
        "search_model": "BM25",
        "task": "Task A"
    }
}

print("\nCreating simulation via API...")
print(f"POST {BASE_URL}/simulations/")

try:
    response = httpx.post(
        f"{BASE_URL}/simulations/",
        json=simulation_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print("\n✅ SUCCESS! Simulation created:")
        print(f"  ID: {result['id']}")
        print(f"  Name: {result['name']}")
        print(f"  Status: {result['status']}")
        print(f"  Config File: {result['config_file_path']}")
        print(f"  Output Directory: {result['output_directory']}")
        
        sim_id = result['id']
        
        # Ask if user wants to start it
        print(f"\nTo start this simulation, run:")
        print(f"  curl -X POST {BASE_URL}/simulations/{sim_id}/control -H 'Content-Type: application/json' -d '{{\"action\": \"start\"}}'")
        print(f"\nTo check status:")
        print(f"  curl {BASE_URL}/simulations/{sim_id}")
        print(f"\nTo view logs:")
        print(f"  curl {BASE_URL}/simulations/{sim_id}/logs?tail=50")
        
    else:
        print("\n❌ FAILED!")
        print(f"Response: {response.text}")
        
except httpx.ConnectError:
    print("\n❌ ERROR: Cannot connect to API server")
    print(f"Make sure the server is running: poetry run simiir-api")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")

