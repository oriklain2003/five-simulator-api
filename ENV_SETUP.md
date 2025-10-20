# Environment Variables Setup

## Quick Setup

1. **Create a `.env` file** in the `simulator_api` folder:

```bash
# Copy the example file
cp env.example .env

# Or create manually
touch .env
```

2. **Edit the `.env` file** with your settings:

```bash
# Simulation API Configuration

# Target API URL - The URL where simulation data will be sent
API_BASE_URL=http://localhost:3001

# API Endpoint for sending object data
OBJECTS_ENDPOINT=/objects/temporary

# Simulation timing settings (in seconds)
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

3. **That's it!** The configuration will be loaded automatically when you start the API.

---

## Configuration Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `API_BASE_URL` | Target API URL where data is sent | `http://localhost:3001` | `http://192.168.1.100:3001` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OBJECTS_ENDPOINT` | API endpoint for objects | `/objects/temporary` | `/api/v1/objects` |
| `TICK_INTERVAL` | Seconds between simulation ticks | `1` | `2` |
| `INACTIVITY_TIMEOUT` | Seconds before marking object inactive | `10` | `15` |

---

## Examples

### Local Development
```bash
API_BASE_URL=http://localhost:3001
OBJECTS_ENDPOINT=/objects/temporary
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

### Remote Server
```bash
API_BASE_URL=http://192.168.1.100:8080
OBJECTS_ENDPOINT=/api/objects
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

### Production
```bash
API_BASE_URL=https://api.example.com
OBJECTS_ENDPOINT=/v1/objects/temporary
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

---

## Verification

When you start the API, you'll see the loaded configuration:

```
📡 API Configuration loaded:
   API_BASE_URL: http://localhost:3001
   OBJECTS_ENDPOINT: /objects/temporary
   TICK_INTERVAL: 1s
   INACTIVITY_TIMEOUT: 10s
```

This confirms your environment variables are loaded correctly!

---

## Troubleshooting

**Configuration not loading?**
- Make sure the `.env` file is in the `simulator_api` folder (same folder as `main.py`)
- Check that `python-dotenv` is installed: `pip install python-dotenv`
- Verify there are no spaces around the `=` sign in your `.env` file

**Using system environment variables instead?**

You can also set these as system environment variables instead of using a `.env` file:

**Windows (PowerShell):**
```powershell
$env:API_BASE_URL="http://localhost:3001"
python main.py
```

**Windows (CMD):**
```cmd
set API_BASE_URL=http://localhost:3001
python main.py
```

**Linux/Mac:**
```bash
export API_BASE_URL=http://localhost:3001
python main.py
```

---

## Security Note

🔒 **Never commit your `.env` file to version control!**

The `.env` file is already added to `.gitignore` to prevent accidental commits.

