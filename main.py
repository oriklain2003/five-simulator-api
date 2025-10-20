"""
FastAPI application for object simulation system
"""

import json
import asyncio
import threading
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from simulator import ObjectSimulator
import send_random_radar
import send_random_radar_decoy
import trigger_drone_attack
import trigger_rocket_attack

# Create FastAPI app
app = FastAPI(
    title="Simulation API",
    description="API for managing radar simulations, drone attacks, rocket attacks, and object tracking",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global state to track running tasks
running_tasks = {
    "random_radar": False,
    "random_radar_decoy": False,
    "main_simulation": False,
    "drone_attack": False,
    "rocket_attack": False
}


class StatusResponse(BaseModel):
    status: str
    message: str


def convert_timestamps(obj):
    """Recursively convert all timestamp fields in the data into datetime objects."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Convert known timestamp formats
            if isinstance(value, str):
                try:
                    # Try parsing ISO-style timestamps
                    obj[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(value, dict) and "seconds" in value and "nanoseconds" in value:
                # Firebase timestamp format
                seconds = value["seconds"]
                nanos = value.get("nanoseconds", 0)
                obj[key] = datetime.fromtimestamp(seconds + nanos / 1e9, tz=timezone.utc)
            else:
                obj[key] = convert_timestamps(value)
    elif isinstance(obj, list):
        obj = [convert_timestamps(item) for item in obj]
    return obj


def load_data_with_timestamps(path):
    """Load JSON file and convert all timestamp-like fields."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return convert_timestamps(data)


# Background task functions
def run_random_radar():
    """Run the random radar generation in background"""
    running_tasks["random_radar"] = True
    try:
        print("Starting random radar generation...")
        # Run the main loop from send_random_radar.py
        batch_number = 1
        while running_tasks["random_radar"]:
            print(f"\n>>> Batch #{batch_number}")
            send_random_radar.send_batch_of_points(num_points=75)
            
            print(f"Waiting 10 seconds before next batch...")
            import time
            for _ in range(10):
                if not running_tasks["random_radar"]:
                    break
                time.sleep(1)
            
            batch_number += 1
    except Exception as e:
        print(f"Error in random radar: {e}")
    finally:
        running_tasks["random_radar"] = False
        print("Random radar stopped")


def run_random_radar_decoy():
    """Run the random radar decoy generation in background"""
    running_tasks["random_radar_decoy"] = True
    try:
        print("Starting random radar decoy generation...")
        # Run the main loop from send_random_radar_decoy.py
        batch_number = 1
        while running_tasks["random_radar_decoy"]:
            print(f"\n>>> Decoy Batch #{batch_number}")
            send_random_radar_decoy.send_batch_of_points(num_points=50)
            
            print(f"Waiting 10 seconds before next batch...")
            import time
            for _ in range(10):
                if not running_tasks["random_radar_decoy"]:
                    break
                time.sleep(1)
            
            batch_number += 1
    except Exception as e:
        print(f"Error in random radar decoy: {e}")
    finally:
        running_tasks["random_radar_decoy"] = False
        print("Random radar decoy stopped")


def run_main_simulation():
    """Run the main simulation with simulated_flights7.json"""
    running_tasks["main_simulation"] = True
    try:
        print("Fetching course data...")
        courses = load_data_with_timestamps("simulated_flights7.json")
        if not courses:
            print("No courses found in the database!")
            return

        print(f"Found {len(courses)} courses")

        # Create and run simulator
        simulator = ObjectSimulator(courses)

        # Modified run loop to check for stop signal
        if not simulator.prepare_simulation():
            return

        print("\n" + "=" * 60)
        print("Starting simulation...")
        print("=" * 60 + "\n")

        import time
        real_start_time = time.time()
        total_duration = simulator._get_total_duration()
        objects_marked_deleted = set()

        while simulator.current_simulation_time <= total_duration and running_tasks["main_simulation"]:
            tick_start = time.time()

            # Get points that should be processed at this time
            points_to_process = simulator._get_points_to_process()

            if points_to_process:
                print(f"[T+{simulator.current_simulation_time:.1f}s] Processing {len(points_to_process)} points...")

                # Group points by object ID
                updates_by_object = {}
                for item in points_to_process:
                    obj_id = item['object_id']
                    if obj_id not in updates_by_object:
                        updates_by_object[obj_id] = []
                    updates_by_object[obj_id].append(item)

                # Update each object and send to API
                for object_id, items in updates_by_object.items():
                    for item in items:
                        simulator._update_object_state(object_id, item['point'])
                        simulator.processed_point_indices.add(item['index'])

                    # Send update after all points for this tick are added
                    simulator._send_object_update(object_id)

            # Check for inactive objects
            inactive_objects = simulator._check_inactive_objects()
            for object_id in inactive_objects:
                if object_id not in objects_marked_deleted:
                    print(f"[T+{simulator.current_simulation_time:.1f}s] Marking inactive object as deleted...")
                    simulator._send_object_update(object_id, is_delete=True)
                    objects_marked_deleted.add(object_id)

            # Move to next time step
            simulator.current_simulation_time += 1  # Using config.TICK_INTERVAL

            # Sleep to maintain real-time simulation
            elapsed = time.time() - tick_start
            sleep_time = max(0, 1 - elapsed)  # Using config.TICK_INTERVAL
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Final summary
        print("\n" + "=" * 60)
        if running_tasks["main_simulation"]:
            print("Simulation complete!")
        else:
            print("Simulation stopped by user!")
        print("=" * 60)
        print(f"Total simulation time: {total_duration:.1f} seconds")
        print(f"Total real time: {time.time() - real_start_time:.1f} seconds")
        print(f"Total points processed: {len(simulator.processed_point_indices)}")
        print(f"Objects marked as deleted: {len(objects_marked_deleted)}")

    finally:
        running_tasks["main_simulation"] = False
        print("Main simulation stopped")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Simulation API",
        "version": "1.0.0",
        "endpoints": {
            "/radar/start": "Start random radar generation",
            "/radar/stop": "Stop random radar generation",
            "/radar/decoy/start": "Start random radar decoy generation",
            "/radar/decoy/stop": "Stop random radar decoy generation",
            "/attack/drone/start": "Trigger a drone attack",
            "/attack/drone/stop": "Stop drone attack",
            "/attack/rocket/start": "Trigger a rocket attack",
            "/attack/rocket/stop": "Stop rocket attack",
            "/simulation/start": "Start main simulation (simulated_flights7.json)",
            "/simulation/stop": "Stop main simulation",
            "/simulation/stop-all": "Stop all running tasks",
            "/simulation/status": "Get status of all running tasks"
        }
    }


@app.post("/radar/start", response_model=StatusResponse)
async def start_random_radar(background_tasks: BackgroundTasks):
    """Start generating random radar points"""
    if running_tasks["random_radar"]:
        raise HTTPException(status_code=400, detail="Random radar is already running")
    
    # Start in background thread
    thread = threading.Thread(target=run_random_radar, daemon=True)
    thread.start()
    
    return StatusResponse(
        status="success",
        message="Random radar generation started"
    )


@app.post("/radar/stop", response_model=StatusResponse)
async def stop_random_radar():
    """Stop generating random radar points"""
    if not running_tasks["random_radar"]:
        raise HTTPException(status_code=400, detail="Random radar is not running")
    
    running_tasks["random_radar"] = False
    
    return StatusResponse(
        status="success",
        message="Random radar generation stopping..."
    )


@app.post("/radar/decoy/start", response_model=StatusResponse)
async def start_random_radar_decoy(background_tasks: BackgroundTasks):
    """Start generating random radar decoy points"""
    if running_tasks["random_radar_decoy"]:
        raise HTTPException(status_code=400, detail="Random radar decoy is already running")
    
    # Start in background thread
    thread = threading.Thread(target=run_random_radar_decoy, daemon=True)
    thread.start()
    
    return StatusResponse(
        status="success",
        message="Random radar decoy generation started"
    )


@app.post("/radar/decoy/stop", response_model=StatusResponse)
async def stop_random_radar_decoy():
    """Stop generating random radar decoy points"""
    if not running_tasks["random_radar_decoy"]:
        raise HTTPException(status_code=400, detail="Random radar decoy is not running")
    
    running_tasks["random_radar_decoy"] = False
    
    return StatusResponse(
        status="success",
        message="Random radar decoy generation stopping..."
    )


def run_drone_attack():
    """Run drone attack in background with stop capability"""
    running_tasks["drone_attack"] = True
    try:
        print("\n🚨 Triggering drone attack...")
        
        # Import required modules
        from all import create_drone_track_simulation
        
        # Create the drone track
        drone_track = create_drone_track_simulation(offset_seconds=10)
        print(f"✅ Drone track created with {len(drone_track.get('points', []))} points")
        
        # Convert timestamps and run with stop checks
        converted_track = convert_timestamps(drone_track)
        simulator = ObjectSimulator([converted_track])
        
        # Run simulation with stop checks (same logic as main simulation)
        if not simulator.prepare_simulation():
            return
        
        print("Starting drone attack simulation...")
        import time
        total_duration = simulator._get_total_duration()
        objects_marked_deleted = set()
        
        while simulator.current_simulation_time <= total_duration and running_tasks["drone_attack"]:
            tick_start = time.time()
            points_to_process = simulator._get_points_to_process()
            
            if points_to_process:
                updates_by_object = {}
                for item in points_to_process:
                    obj_id = item['object_id']
                    if obj_id not in updates_by_object:
                        updates_by_object[obj_id] = []
                    updates_by_object[obj_id].append(item)
                
                for object_id, items in updates_by_object.items():
                    for item in items:
                        simulator._update_object_state(object_id, item['point'])
                        simulator.processed_point_indices.add(item['index'])
                    simulator._send_object_update(object_id)
            
            inactive_objects = simulator._check_inactive_objects()
            for object_id in inactive_objects:
                if object_id not in objects_marked_deleted:
                    simulator._send_object_update(object_id, is_delete=True)
                    objects_marked_deleted.add(object_id)
            
            simulator.current_simulation_time += 1
            elapsed = time.time() - tick_start
            sleep_time = max(0, 1 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        if running_tasks["drone_attack"]:
            print("✅ Drone attack completed!")
        else:
            print("⚠️  Drone attack stopped by user")
            
    except Exception as e:
        print(f"Error in drone attack: {e}")
        import traceback
        traceback.print_exc()
    finally:
        running_tasks["drone_attack"] = False
        print("Drone attack simulation ended")


@app.post("/attack/drone/start", response_model=StatusResponse)
async def start_drone_attack():
    """Trigger a drone attack simulation"""
    if running_tasks["drone_attack"]:
        raise HTTPException(status_code=400, detail="Drone attack is already running")
    
    try:
        # Run the drone attack trigger in background
        thread = threading.Thread(
            target=run_drone_attack,
            daemon=True
        )
        thread.start()
        
        return StatusResponse(
            status="success",
            message="Drone attack triggered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger drone attack: {str(e)}")


@app.post("/attack/drone/stop", response_model=StatusResponse)
async def stop_drone_attack():
    """Stop drone attack simulation"""
    if not running_tasks["drone_attack"]:
        raise HTTPException(status_code=400, detail="Drone attack is not running")
    
    running_tasks["drone_attack"] = False
    
    return StatusResponse(
        status="success",
        message="Drone attack stopping..."
    )


def run_rocket_attack():
    """Run rocket attack in background with stop capability"""
    running_tasks["rocket_attack"] = True
    try:
        print("\n🚀 Triggering rocket attack...")
        
        # Create the rocket track (from trigger_rocket_attack.py logic)
        rocket_track = trigger_rocket_attack.create_rocket_track_simulation(
            start_lat=32.270878,
            start_lon=36.018677,
            end_lat=32.245329,
            end_lon=35.529785,
            offset_seconds=1
        )
        print(f"✅ Rocket track created with {len(rocket_track.get('points', []))} points")
        
        # Convert timestamps and run with stop checks
        converted_track = convert_timestamps(rocket_track)
        simulator = ObjectSimulator([converted_track])
        
        # Run simulation with stop checks (same logic as main simulation)
        if not simulator.prepare_simulation():
            return
        
        print("Starting rocket attack simulation...")
        import time
        total_duration = simulator._get_total_duration()
        objects_marked_deleted = set()
        
        while simulator.current_simulation_time <= total_duration and running_tasks["rocket_attack"]:
            tick_start = time.time()
            points_to_process = simulator._get_points_to_process()
            
            if points_to_process:
                updates_by_object = {}
                for item in points_to_process:
                    obj_id = item['object_id']
                    if obj_id not in updates_by_object:
                        updates_by_object[obj_id] = []
                    updates_by_object[obj_id].append(item)
                
                for object_id, items in updates_by_object.items():
                    for item in items:
                        simulator._update_object_state(object_id, item['point'])
                        simulator.processed_point_indices.add(item['index'])
                    simulator._send_object_update(object_id)
            
            inactive_objects = simulator._check_inactive_objects()
            for object_id in inactive_objects:
                if object_id not in objects_marked_deleted:
                    simulator._send_object_update(object_id, is_delete=True)
                    objects_marked_deleted.add(object_id)
            
            simulator.current_simulation_time += 1
            elapsed = time.time() - tick_start
            sleep_time = max(0, 1 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        if running_tasks["rocket_attack"]:
            print("✅ Rocket attack completed!")
        else:
            print("⚠️  Rocket attack stopped by user")
            
    except Exception as e:
        print(f"Error in rocket attack: {e}")
        import traceback
        traceback.print_exc()
    finally:
        running_tasks["rocket_attack"] = False
        print("Rocket attack simulation ended")


@app.post("/attack/rocket/start", response_model=StatusResponse)
async def start_rocket_attack():
    """Trigger a rocket attack simulation"""
    if running_tasks["rocket_attack"]:
        raise HTTPException(status_code=400, detail="Rocket attack is already running")
    
    try:
        # Run the rocket attack trigger in background
        thread = threading.Thread(
            target=run_rocket_attack,
            daemon=True
        )
        thread.start()
        
        return StatusResponse(
            status="success",
            message="Rocket attack triggered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger rocket attack: {str(e)}")


@app.post("/attack/rocket/stop", response_model=StatusResponse)
async def stop_rocket_attack():
    """Stop rocket attack simulation"""
    if not running_tasks["rocket_attack"]:
        raise HTTPException(status_code=400, detail="Rocket attack is not running")
    
    running_tasks["rocket_attack"] = False
    
    return StatusResponse(
        status="success",
        message="Rocket attack stopping..."
    )


@app.post("/simulation/start", response_model=StatusResponse)
async def start_main_simulation():
    """Start the main simulation using simulated_flights7.json"""
    if running_tasks["main_simulation"]:
        raise HTTPException(status_code=400, detail="Main simulation is already running")
    
    # Start in background thread
    thread = threading.Thread(target=run_main_simulation, daemon=True)
    thread.start()
    
    return StatusResponse(
        status="success",
        message="Main simulation started with simulated_flights7.json"
    )


@app.post("/simulation/stop", response_model=StatusResponse)
async def stop_main_simulation():
    """Stop the main simulation"""
    if not running_tasks["main_simulation"]:
        raise HTTPException(status_code=400, detail="Main simulation is not running")
    
    running_tasks["main_simulation"] = False
    
    return StatusResponse(
        status="success",
        message="Main simulation stopping..."
    )


@app.post("/simulation/stop-all", response_model=StatusResponse)
async def stop_all_simulations():
    """Stop all running simulations and tasks"""
    stopped_tasks = []
    
    if running_tasks["random_radar"]:
        running_tasks["random_radar"] = False
        stopped_tasks.append("random_radar")
    
    if running_tasks["random_radar_decoy"]:
        running_tasks["random_radar_decoy"] = False
        stopped_tasks.append("random_radar_decoy")
    
    if running_tasks["main_simulation"]:
        running_tasks["main_simulation"] = False
        stopped_tasks.append("main_simulation")
    
    if running_tasks["drone_attack"]:
        running_tasks["drone_attack"] = False
        stopped_tasks.append("drone_attack")
    
    if running_tasks["rocket_attack"]:
        running_tasks["rocket_attack"] = False
        stopped_tasks.append("rocket_attack")
    
    if not stopped_tasks:
        return StatusResponse(
            status="success",
            message="No tasks were running"
        )
    
    return StatusResponse(
        status="success",
        message=f"Stopping all tasks: {', '.join(stopped_tasks)}"
    )


@app.get("/simulation/status")
async def get_simulation_status():
    """Get the status of all running tasks"""
    return {
        "random_radar": "running" if running_tasks["random_radar"] else "stopped",
        "random_radar_decoy": "running" if running_tasks["random_radar_decoy"] else "stopped",
        "main_simulation": "running" if running_tasks["main_simulation"] else "stopped",
        "drone_attack": "running" if running_tasks["drone_attack"] else "stopped",
        "rocket_attack": "running" if running_tasks["rocket_attack"] else "stopped"
    }


if __name__ == "__main__":
    import uvicorn
    print("="*70)
    print("SIMULATION API SERVER")
    print("="*70)
    print("\nAvailable endpoints:")
    print("  POST /radar/start           - Start random radar")
    print("  POST /radar/stop            - Stop random radar")
    print("  POST /radar/decoy/start     - Start random radar decoy")
    print("  POST /radar/decoy/stop      - Stop random radar decoy")
    print("  POST /attack/drone/start    - Trigger drone attack")
    print("  POST /attack/drone/stop     - Stop drone attack")
    print("  POST /attack/rocket/start   - Trigger rocket attack")
    print("  POST /attack/rocket/stop    - Stop rocket attack")
    print("  POST /simulation/start      - Start main simulation")
    print("  POST /simulation/stop       - Stop main simulation")
    print("  POST /simulation/stop-all   - Stop ALL running tasks")
    print("  GET  /simulation/status     - Get status of tasks")
    print("\nDocs available at: http://localhost:8000/docs")
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=80)
