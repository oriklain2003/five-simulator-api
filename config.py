"""
Configuration settings for the simulation
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Firebase settings
SERVICE_ACCOUNT_PATH = 'dataaa/genareft/servicelogin.json'
COLLECTION_NAME = 'courses'
DOCUMENT_ID = 'X3Rg6eFxI6aS7lDARwxh'  # Optional: specific document ID

# API settings - loaded from environment variables
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3001')
OBJECTS_ENDPOINT = os.getenv('OBJECTS_ENDPOINT', '/objects/temporary')

# Simulation settings
TICK_INTERVAL = int(os.getenv('TICK_INTERVAL', '1'))  # seconds between checks
INACTIVITY_TIMEOUT = int(os.getenv('INACTIVITY_TIMEOUT', '10'))  # seconds of inactivity before marking as deleted

# Print loaded configuration on import (helpful for debugging)
if __name__ != "__main__":
    print(f"📡 API Configuration loaded:")
    print(f"   API_BASE_URL: {API_BASE_URL}")
    print(f"   OBJECTS_ENDPOINT: {OBJECTS_ENDPOINT}")
    print(f"   TICK_INTERVAL: {TICK_INTERVAL}s")
    print(f"   INACTIVITY_TIMEOUT: {INACTIVITY_TIMEOUT}s")

