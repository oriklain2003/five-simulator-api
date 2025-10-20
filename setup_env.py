"""
Quick setup script to create .env file
"""
import os

def create_env_file():
    """Create a .env file with default values"""
    
    env_content = """# Simulation API Configuration
# Update these values according to your environment

# Target API URL - The URL where simulation data will be sent
API_BASE_URL=http://localhost:3001

# API Endpoint for sending object data
OBJECTS_ENDPOINT=/objects/temporary

# Simulation timing settings (in seconds)
TICK_INTERVAL=1
INACTIVITY_TIMEOUT=10
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print(f"📁 Location: {env_path}")
    print("\n📝 Default configuration:")
    print("   OBJECTS_ENDPOINT: /objects/temporary")
    print("   TICK_INTERVAL: 1")
    print("   INACTIVITY_TIMEOUT: 10")
    print("\nYou can now edit the .env file to customize these values.")


if __name__ == "__main__":
    print("="*60)
    print("Environment Setup Script")
    print("="*60)
    print("\nThis script will create a .env file with default settings.")
    print()
    
    create_env_file()
    
    print("\n" + "="*60)
    print("Next steps:")
    print("1. Edit .env file if you need to change the API URL")
    print("2. Run: python main.py")
    print("="*60)


