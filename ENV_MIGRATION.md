# Migration to Environment Variables

## ✅ What Changed

The API endpoint URL and other configuration settings are now loaded from **environment variables** instead of being hardcoded in `config.py`.

### Before:
```python
# config.py
API_BASE_URL = 'http://localhost:3001'  # Hardcoded
OBJECTS_ENDPOINT = '/objects/temporary'
```

### After:
```python
# config.py
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3001')  # From .env
OBJECTS_ENDPOINT = os.getenv('OBJECTS_ENDPOINT', '/objects/temporary')
```

## 🎯 Benefits

✅ **Security**: No hardcoded URLs in code  
✅ **Flexibility**: Easy to change without editing code  
✅ **Environment-specific**: Different URLs for dev/staging/prod  
✅ **Team-friendly**: Each developer can have their own settings  

## 🚀 Quick Setup

### Option 1: Automatic Setup (Recommended)

```bash
cd simulator_api
python setup_env.py
```

This creates a `.env` file with default values. Edit it as needed!

### Option 2: Manual Setup

```bash
# Copy the example file
cp env.example .env

# Edit with your favorite editor
nano .env
# or
notepad .env
```

### Option 3: Use System Environment Variables

**Windows (PowerShell):**
```powershell
$env:API_BASE_URL="http://192.168.1.100:3001"
python main.py
```

**Linux/Mac:**
```bash
export API_BASE_URL="http://192.168.1.100:3001"
python main.py
```

## 📝 .env File Format

Create a file named `.env` in the `simulator_api` folder:

```bash
# Target API - where simulation data is sent
API_BASE_URL=http://localhost:3001

# Endpoint path
OBJECTS_ENDPOINT=/objects/temporary

# Timing settings (seconds)
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
```

## 🔍 Verification

When you start the API, you'll see:

```
📡 API Configuration loaded:
   API_BASE_URL: http://localhost:3001
   OBJECTS_ENDPOINT: /objects/temporary
   TICK_INTERVAL: 1s
   INACTIVITY_TIMEOUT: 10s
```

This confirms your settings are loaded correctly!

## 📋 All Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_BASE_URL` | Target API URL | `http://localhost:3001` | No |
| `OBJECTS_ENDPOINT` | Objects endpoint path | `/objects/temporary` | No |
| `TICK_INTERVAL` | Simulation tick interval (seconds) | `1` | No |
| `INACTIVITY_TIMEOUT` | Object timeout (seconds) | `10` | No |

All variables have sensible defaults, so the API works out-of-the-box!

## 🔐 Security Notes

✅ `.env` is already in `.gitignore` - it won't be committed  
✅ Each developer/server can have different settings  
✅ No secrets in source code  

## 🛠️ Files Created/Modified

### Created:
- ✅ `env.example` - Template for .env file
- ✅ `ENV_SETUP.md` - Detailed configuration guide
- ✅ `ENV_MIGRATION.md` - This file!
- ✅ `setup_env.py` - Automatic setup script
- ✅ `.gitignore` - Prevents .env from being committed

### Modified:
- ✅ `config.py` - Now loads from environment variables
- ✅ `requirements.txt` - Added `python-dotenv`
- ✅ `README.md` - Added configuration section
- ✅ `QUICK_START.md` - Added setup step

## 🎓 Usage Examples

### Development (Local)
```bash
API_BASE_URL=http://localhost:3001
```

### Staging
```bash
API_BASE_URL=http://staging.example.com:3001
```

### Production
```bash
API_BASE_URL=https://api.production.com
OBJECTS_ENDPOINT=/api/v2/objects
```

### Team Member with Different Port
```bash
API_BASE_URL=http://localhost:8080
```

## ❓ Troubleshooting

**Problem**: Changes to .env not reflected

**Solution**: Restart the API server (it loads .env on startup)

---

**Problem**: Getting connection errors

**Solution**: Check your `API_BASE_URL` in .env matches your target API

---

**Problem**: .env file not found

**Solution**: Run `python setup_env.py` or create it manually

---

**Problem**: Want to use different settings temporarily

**Solution**: Set environment variables before running:
```bash
API_BASE_URL=http://192.168.1.50:3001 python main.py
```

## 📖 More Information

- **Full setup guide**: See `ENV_SETUP.md`
- **Quick start**: See `QUICK_START.md`
- **API docs**: See `README.md`

---

**No breaking changes!** Everything works the same, just more flexible! 🎉

