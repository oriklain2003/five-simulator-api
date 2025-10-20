"""
Manual Drone Attack Trigger

This script manually triggers a drone attack simulation by:
1. Sending 4 radar points (10s wait, then 1s intervals)
2. Sending the drone track path directly to the API

Run this whenever you want to simulate a drone attack!
"""
import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta

from simulator_api.config import API_BASE_URL

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataaa', 'genareft'))

from all import create_drone_track_simulation, send_radar_points_with_timing

def send_drone_track_to_api():
    """
    Create and send the drone track directly to the API
    
    Args:
        api_url: Base URL of the API
    """
    print("\n" + "="*60)
    print("CREATING DRONE TRACK")
    print("="*60)
    
    # Create the drone track with proper timing (appears at current time + 1 second)
    drone_track = create_drone_track_simulation(offset_seconds=10)
    
    print(f"✅ Drone track created:")
    print(f"   ID: {drone_track['_id']}")
    print(f"   Type: {drone_track['object_type']}")
    print(f"   Points: {len(drone_track['points'])}")
    print(f"   First point: {drone_track['points'][0]['timestamp']}")
    
    # Transform to API schema
    from simulator import ObjectSimulator
    
    # Create a temporary simulator instance just to use the transform method
    temp_sim = ObjectSimulator([])
    
    # Prepare payload
    payload = {
        'object_id': drone_track['_id'],
        'is_delete': False,
        **drone_track
    }
    
    # Transform to API schema
    schema_obj = temp_sim.transform_to_schema(payload)
    
    print("\n" + "="*60)
    print("SENDING DRONE TRACK TO API")
    print("="*60)
    
    try:

        sim = ObjectSimulator([convert_timestamps(drone_track)])
        sim.run()

        print(f"✅ Classification suggestion sent successfully!")
        # print(f"   Suggested: {classification_info.get('suggested_identification', 'drone')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending drone track: {e}")
        return False
    
    return True

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

def main():
    """
    Main function to trigger the drone attack
    """
    print("\n" + "🚨"*30)
    print("DRONE ATTACK TRIGGER")
    print("🚨"*30)
    
    print("\nThis script will:")
    print("  1. Wait 10 seconds")
    print("  2. Send 4 radar points (1 second apart)")
    print("  3. Send the drone track to the API")
    print("\n" + "="*60)
    
    # input("Press Enter to trigger the drone attack...")
    
    print("\n" + "="*60)
    print("PHASE 1: RADAR DETECTION")
    print("="*60)
    
    # Send radar points
    try:
        send_radar_points_with_timing(API_BASE_URL)
    except Exception as e:
        print(f"❌ Error sending radar points: {e}")
        print("Continuing with drone track anyway...")
    
    print("\n" + "="*60)
    print("PHASE 2: TRACKED OBJECT")
    print("="*60)
    print("Waiting 1 second after radar points...")
    time.sleep(1)
    
    # Send drone track
    success = send_drone_track_to_api()
    
    # Final summary
    print("\n" + "="*60)
    if success:
        print("✅ DRONE ATTACK TRIGGERED SUCCESSFULLY!")
    else:
        print("⚠️  DRONE ATTACK PARTIALLY FAILED")
    print("="*60)
    
    print("\nTimeline:")
    print("  T+0s  : Script started")
    print("  T+10s : Radar point 1 sent")
    print("  T+11s : Radar point 2 sent")
    print("  T+12s : Radar point 3 sent")
    print("  T+13s : Radar point 4 sent")
    print("  T+14s : Drone track sent to API ✈️")
    print("  T+14s : Classification suggested 🎯")
    
    print("\nCheck your radar display for the new threat!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

