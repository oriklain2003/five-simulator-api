# API Usage Examples

Quick reference for calling all API endpoints.

## Using curl

### 1. Check API Status
```bash
curl http://localhost:8000/
```

### 2. Start Random Radar
```bash
curl -X POST http://localhost:8000/radar/start
```

Response:
```json
{
  "status": "success",
  "message": "Random radar generation started"
}
```

### 3. Stop Random Radar
```bash
curl -X POST http://localhost:8000/radar/stop
```

### 4. Start Random Radar Decoy
```bash
curl -X POST http://localhost:8000/radar/decoy/start
```

### 5. Stop Random Radar Decoy
```bash
curl -X POST http://localhost:8000/radar/decoy/stop
```

### 6. Start Drone Attack
```bash
curl -X POST http://localhost:8000/attack/drone/start
```

### 7. Stop Drone Attack
```bash
curl -X POST http://localhost:8000/attack/drone/stop
```

### 8. Start Rocket Attack
```bash
curl -X POST http://localhost:8000/attack/rocket/start
```

### 9. Stop Rocket Attack
```bash
curl -X POST http://localhost:8000/attack/rocket/stop
```

### 10. Start Main Simulation
```bash
curl -X POST http://localhost:8000/simulation/start
```

### 11. Stop Main Simulation
```bash
curl -X POST http://localhost:8000/simulation/stop
```

### 12. Stop All Tasks (Quick Reset)
```bash
curl -X POST http://localhost:8000/simulation/stop-all
```

Response:
```json
{
  "status": "success",
  "message": "Stopping all tasks: random_radar, main_simulation, drone_attack"
}
```

### 13. Check Simulation Status
```bash
curl http://localhost:8000/simulation/status
```

Response:
```json
{
  "random_radar": "running",
  "random_radar_decoy": "stopped",
  "main_simulation": "running",
  "drone_attack": "stopped",
  "rocket_attack": "stopped"
}
```

## Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Start random radar
response = requests.post(f"{BASE_URL}/radar/start")
print(response.json())

# Start main simulation
response = requests.post(f"{BASE_URL}/simulation/start")
print(response.json())

# Trigger drone attack
response = requests.post(f"{BASE_URL}/attack/drone/start")
print(response.json())

# Check status
response = requests.get(f"{BASE_URL}/simulation/status")
print(response.json())

# Stop drone attack
response = requests.post(f"{BASE_URL}/attack/drone/stop")
print(response.json())

# Stop main simulation (for reset)
response = requests.post(f"{BASE_URL}/simulation/stop")
print(response.json())

# Stop random radar
response = requests.post(f"{BASE_URL}/radar/stop")
print(response.json())
```

## Using PowerShell

```powershell
# Start random radar
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/radar/start"

# Start main simulation
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/simulation/start"

# Trigger drone attack
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/attack/drone/start"

# Check status
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/simulation/status"

# Stop drone attack
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/attack/drone/stop"

# Stop main simulation
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/simulation/stop"

# Stop random radar
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/radar/stop"
```

## Using JavaScript (Browser/Node.js)

```javascript
const BASE_URL = "http://localhost:8000";

// Start random radar
fetch(`${BASE_URL}/radar/start`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));

// Start main simulation
fetch(`${BASE_URL}/simulation/start`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));

// Trigger drone attack
fetch(`${BASE_URL}/attack/drone/start`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));

// Check status
fetch(`${BASE_URL}/simulation/status`)
  .then(res => res.json())
  .then(data => console.log(data));

// Stop drone attack
fetch(`${BASE_URL}/attack/drone/stop`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));

// Stop main simulation
fetch(`${BASE_URL}/simulation/stop`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));
```

## Common Workflows

### Full Simulation Start
```bash
# Start the main simulation with all objects
curl -X POST http://localhost:8000/simulation/start

# Add random radar noise
curl -X POST http://localhost:8000/radar/start

# Add decoy radar points
curl -X POST http://localhost:8000/radar/decoy/start
```

### Attack Scenario
```bash
# Start with clean slate
curl -X POST http://localhost:8000/simulation/start

# Wait a bit, then trigger drone attack
sleep 30
curl -X POST http://localhost:8000/attack/drone/start

# Wait a bit more, then trigger rocket attack
sleep 60
curl -X POST http://localhost:8000/attack/rocket/start
```

### Reset and Restart Simulation
```bash
# Stop current simulation
curl -X POST http://localhost:8000/simulation/stop

# Wait a moment for cleanup
sleep 2

# Start fresh simulation
curl -X POST http://localhost:8000/simulation/start
```

### Stop Everything (Quick Method)
```bash
# Stop everything at once!
curl -X POST http://localhost:8000/simulation/stop-all

# Verify everything is stopped
curl http://localhost:8000/simulation/status
```

### Stop Everything (Manual Method)
```bash
# Stop each component individually
curl -X POST http://localhost:8000/radar/stop
curl -X POST http://localhost:8000/radar/decoy/stop
curl -X POST http://localhost:8000/simulation/stop
curl -X POST http://localhost:8000/attack/drone/stop
curl -X POST http://localhost:8000/attack/rocket/stop

# Verify everything is stopped
curl http://localhost:8000/simulation/status
```

## Interactive Documentation

For the easiest way to test the API, visit the auto-generated documentation at:

**http://localhost:8000/docs**

This provides a web interface where you can:
- See all endpoints
- Try them directly in your browser
- View request/response formats
- No command line needed!

