# Simulation API

A FastAPI-based REST API for managing radar simulations, drone attacks, rocket attacks, and object tracking.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** (create a `.env` file):
```bash
# Copy the example file
cp env.example .env

# Edit .env with your settings
# API_BASE_URL=http://localhost:3001
# OBJECTS_ENDPOINT=/objects/temporary
```

See `ENV_SETUP.md` for detailed configuration instructions.

## Running the API

Start the API server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

Interactive API documentation (Swagger UI) will be available at: `http://localhost:8000/docs`

## API Endpoints

### Random Radar

#### Start Random Radar
```bash
POST /radar/start
```

Starts generating random radar points. Sends 75 random points every 10 seconds within the configured polygon boundaries.

**Example:**
```bash
curl -X POST http://localhost:8000/radar/start
```

#### Stop Random Radar
```bash
POST /radar/stop
```

Stops the random radar generation.

**Example:**
```bash
curl -X POST http://localhost:8000/radar/stop
```

### Random Radar Decoy

#### Start Random Radar Decoy
```bash
POST /radar/decoy/start
```

Starts generating random radar decoy points. Sends 50 random points every 10 seconds.

**Example:**
```bash
curl -X POST http://localhost:8000/radar/decoy/start
```

#### Stop Random Radar Decoy
```bash
POST /radar/decoy/stop
```

Stops the random radar decoy generation.

**Example:**
```bash
curl -X POST http://localhost:8000/radar/decoy/stop
```

### Attack Simulation

#### Start Drone Attack
```bash
POST /attack/drone/start
```

Triggers a drone attack simulation. This will:
1. Send 4 radar points (with timing)
2. Send a drone track to the API
3. Include classification suggestion

**Example:**
```bash
curl -X POST http://localhost:8000/attack/drone/start
```

#### Stop Drone Attack
```bash
POST /attack/drone/stop
```

Stops a running drone attack simulation.

**Example:**
```bash
curl -X POST http://localhost:8000/attack/drone/stop
```

#### Start Rocket Attack
```bash
POST /attack/rocket/start
```

Triggers a rocket attack simulation. This will:
1. Create a rocket trajectory
2. Send the rocket track to the API
3. Classify it as a rocket

**Example:**
```bash
curl -X POST http://localhost:8000/attack/rocket/start
```

#### Stop Rocket Attack
```bash
POST /attack/rocket/stop
```

Stops a running rocket attack simulation.

**Example:**
```bash
curl -X POST http://localhost:8000/attack/rocket/stop
```

### Main Simulation

#### Start Main Simulation
```bash
POST /simulation/start
```

Starts the main object simulation using `simulated_flights7.json`. This runs the full simulation with all course data.

**Example:**
```bash
curl -X POST http://localhost:8000/simulation/start
```

#### Stop Main Simulation
```bash
POST /simulation/stop
```

Stops the currently running main simulation. Useful for resetting and restarting the simulation.

**Example:**
```bash
curl -X POST http://localhost:8000/simulation/stop
```

#### Stop All Tasks
```bash
POST /simulation/stop-all
```

Stops ALL running tasks at once (radar, decoy, main simulation, and attacks). Perfect for quick resets!

**Example:**
```bash
curl -X POST http://localhost:8000/simulation/stop-all
```

**Response:**
```json
{
  "status": "success",
  "message": "Stopping all tasks: random_radar, main_simulation, drone_attack"
}
```

#### Get Simulation Status
```bash
GET /simulation/status
```

Returns the status of all running tasks.

**Example:**
```bash
curl http://localhost:8000/simulation/status
```

**Response:**
```json
{
  "random_radar": "running",
  "random_radar_decoy": "stopped",
  "main_simulation": "running",
  "drone_attack": "stopped",
  "rocket_attack": "stopped"
}
```

## Configuration

Configuration is managed through **environment variables** for security and flexibility.

### Method 1: Using .env file (Recommended)

Create a `.env` file in the `simulator_api` folder:

```bash
API_BASE_URL=http://localhost:3001
OBJECTS_ENDPOINT=/objects/temporary
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

### Method 2: System environment variables

**Windows (PowerShell):**
```powershell
$env:API_BASE_URL="http://localhost:3001"
```

**Linux/Mac:**
```bash
export API_BASE_URL=http://localhost:3001
```

### Configuration Variables

- **API_BASE_URL**: Target API URL where data is sent (default: `http://localhost:3001`)
- **OBJECTS_ENDPOINT**: API endpoint for objects (default: `/objects/temporary`)
- **TICK_INTERVAL**: Seconds between simulation ticks (default: `1`)
- **INACTIVITY_TIMEOUT**: Seconds before marking objects as inactive (default: `10`)

📖 **Full configuration guide**: See `ENV_SETUP.md`

## File Structure

```
simulator_api/
├── main.py                      # FastAPI application
├── simulator.py                 # Core simulation logic
├── config.py                    # Configuration settings
├── send_random_radar.py         # Random radar generator
├── send_random_radar_decoy.py   # Random radar decoy generator
├── trigger_drone_attack.py      # Drone attack trigger
├── trigger_rocket_attack.py     # Rocket attack trigger
├── simulated_flights7.json      # Main simulation data
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Notes

- All background tasks (random radar, decoy, main simulation) run in separate daemon threads
- Attack triggers (drone/rocket) are one-time events that run in background
- Make sure your target API (default: `http://localhost:3001`) is running before starting simulations
- The API uses thread-based concurrency for background tasks

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can:
- View all available endpoints
- Test endpoints directly from the browser
- See request/response schemas
- View detailed endpoint descriptions

