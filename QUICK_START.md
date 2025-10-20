# Quick Start Guide

Get your simulation API up and running in 3 steps!

## Step 1: Install Dependencies

```bash
cd simulator_api
pip install -r requirements.txt
```

## Step 2: Configure Environment (Optional)

Create a `.env` file to customize your API endpoint:

```bash
# Copy the example
cp env.example .env

# Edit .env with your target API URL
# API_BASE_URL=http://localhost:3001
```

> If you skip this step, it will use the default: `http://localhost:3001`

## Step 3: Start the API

```bash
python main.py
```

The API will start on `http://localhost:8000`

## Step 4: Test It!

Open your browser and go to:
```
http://localhost:8000/docs
```

This opens the interactive Swagger UI where you can test all endpoints with a click!

---

## Most Common Commands

### Start Everything
```bash
# Start the main simulation
curl -X POST http://localhost:8000/simulation/start

# Add some radar noise
curl -X POST http://localhost:8000/radar/start
```

### Trigger Attacks
```bash
# Drone attack
curl -X POST http://localhost:8000/attack/drone/start

# Rocket attack
curl -X POST http://localhost:8000/attack/rocket/start
```

### Stop Everything (Reset)
```bash
# One command to stop all running tasks!
curl -X POST http://localhost:8000/simulation/stop-all
```

### Check What's Running
```bash
curl http://localhost:8000/simulation/status
```

---

## All Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/radar/start` | Start random radar generation |
| POST | `/radar/stop` | Stop random radar |
| POST | `/radar/decoy/start` | Start radar decoy |
| POST | `/radar/decoy/stop` | Stop radar decoy |
| POST | `/attack/drone/start` | Trigger drone attack |
| POST | `/attack/drone/stop` | Stop drone attack |
| POST | `/attack/rocket/start` | Trigger rocket attack |
| POST | `/attack/rocket/stop` | Stop rocket attack |
| POST | `/simulation/start` | Start main simulation |
| POST | `/simulation/stop` | Stop main simulation |
| POST | `/simulation/stop-all` | **Stop ALL tasks** ⚡ |
| GET | `/simulation/status` | Check status of all tasks |

---

## Tips

✅ **Use the interactive docs**: `http://localhost:8000/docs` - No command line needed!

✅ **Quick reset**: Use `/simulation/stop-all` to stop everything at once

✅ **Check status**: Use `/simulation/status` to see what's currently running

✅ **Multiple attacks**: You can run drone and rocket attacks simultaneously

✅ **Combine tasks**: Run radar, decoy, and main simulation together for realistic scenarios

---

## Need More Details?

- **Full documentation**: See `README.md`
- **API examples**: See `API_EXAMPLES.md`
- **Configuration**: Edit `config.py`

---

## Troubleshooting

**Port already in use?**
```bash
# Change the port in main.py (last line):
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8000 to 8001
```

**Can't connect to target API?**
- Make sure your target API (default: `http://localhost:3001`) is running
- Edit `config.py` to change the API_BASE_URL

**Task won't start?**
- Check if it's already running: `curl http://localhost:8000/simulation/status`
- Stop it first: `curl -X POST http://localhost:8000/simulation/stop-all`
- Then try starting again

---

Happy simulating! 🚀

