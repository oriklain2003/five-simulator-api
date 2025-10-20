"""
Manual Rocket Attack Trigger

This script manually triggers a rocket attack simulation by:
1. Sending the rocket track path directly to the API
2. Sending a classification message identifying it as a rocket

Run this whenever you want to simulate a rocket attack!
"""
import sys
import os
import time
import requests
import json
import uuid
import math
from datetime import datetime, timedelta, timezone

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dataaa', 'genareft'))

from simulator import ObjectSimulator


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing between two points"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def move_point(lat, lon, speed, brg, dt=1):
    """Move a point by distance based on speed and bearing"""
    R = 6371000
    distance = speed * dt
    brg = math.radians(brg)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) + math.cos(lat1) * math.sin(distance / R) * math.cos(brg))
    lon2 = lon1 + math.atan2(math.sin(brg) * math.sin(distance / R) * math.cos(lat1),
                             math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def create_rocket_track_simulation(start_lat, start_lon, end_lat, end_lon, offset_seconds=1):
    """
    Create a rocket track from start to end position
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Ending latitude
        end_lon: Ending longitude
        offset_seconds: Seconds to offset from current time
    """
    # Rocket parameters
    speed_kts = 300  # Rockets are very fast (approx 770 m/s = 1500 knots)
    speed_mps = speed_kts * 0.514444
    altitude = 5000  # Typical rocket altitude in feet
    
    # Calculate total distance
    total_distance = haversine(start_lat, start_lon, end_lat, end_lon)
    
    # Create trajectory points
    points = []
    base_time = datetime.utcnow()
    offset_time = base_time + timedelta(seconds=offset_seconds)
    timestamp = offset_time
    
    current_lat, current_lon = start_lat, start_lon
    point_idx = 0
    
    # Generate points along the path
    while haversine(current_lat, current_lon, end_lat, end_lon) > speed_mps * 10:  # 10 second intervals
        brg = bearing(current_lat, current_lon, end_lat, end_lon)
        current_lat, current_lon = move_point(current_lat, current_lon, speed_mps, brg, dt=10)
        
        points.append({
            "timestamp": timestamp.isoformat() + "+00:00",
            "lat": current_lat,
            "lon": current_lon,
            "altitude": altitude,
            "speed_kts": speed_kts,
            "bearing": brg,
            "rotation": brg - 90,  # Add rotation for visualization
            "point_id": f"p{point_idx}"
        })
        
        timestamp += timedelta(seconds=10)
        point_idx += 1
    
    # Add final point at destination
    final_bearing = bearing(current_lat, current_lon, end_lat, end_lon)
    points.append({
        "timestamp": timestamp.isoformat() + "+00:00",
        "lat": end_lat,
        "lon": end_lon,
        "altitude": altitude,
        "speed_kts": speed_kts,
        "bearing": final_bearing,
        "rotation": final_bearing - 90,  # Add rotation for visualization
        "point_id": f"p{point_idx}"
    })
    
    rocket_track = {
        "_id": str(uuid.uuid4()),
        "object_type": "arrow",
        "color_on_map": "#FF4500",  # Orange-red color for rocket
        "created_at": offset_time.isoformat() + "+00:00",
        "updated_at": offset_time.isoformat() + "+00:00",
        "avg_speed": speed_kts,
        "altitude": altitude,
        "rotation": points[2]["rotation"],
        "starting_point": {"lat": start_lat, "lon": start_lon},
        "ending_point": {"lat": end_lat, "lon": end_lon},
        "total_distance": int(total_distance),
        "total_distance_simulated": int(total_distance),
        "total_direction_changes": 0,
        "total_speed_changes": 0,
        "total_altitude_changes": 0,
        "points": points,
        "detailedMessage":"התגלתה מטרה מהירה 5 מייל צפונית צפונית לקו גבול לבנון.",
        "type": "arrow",
        "name": "טיל שיוט",  # Name: Ballistic missile
        "originCountry": "צפון ירדן",
        "moving_to":"מזרח המדינה",
        "should_classify": True,
        "steps":[
            {
                "question":"נראה שיש פה אירוע משולב תרצה שאתדרך אותך?",
                "answers": ["""יש לעלות מטוסי קרב לאוויר לפטרולי גילוי ויירוט.
יש להודיע למפקדים בכירים.
ויש לעלות כוננות של כל הסללות הפרוסות בצפון."""]}        ],
        "classification_info": {
            "suggested_identification": "rocket",
            "suggestion_reason": "High-speed projectile detected with ballistic trajectory characteristics"
        }
    }
    
    return rocket_track



def convert_timestamps(obj):
    """Recursively convert all timestamp fields in the data into datetime objects."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                try:
                    obj[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(value, dict) and "seconds" in value and "nanoseconds" in value:
                seconds = value["seconds"]
                nanos = value.get("nanoseconds", 0)
                obj[key] = datetime.fromtimestamp(seconds + nanos / 1e9, tz=timezone.utc)
            else:
                obj[key] = convert_timestamps(value)
    elif isinstance(obj, list):
        obj = [convert_timestamps(item) for item in obj]
    return obj


def send_rocket_track_to_api():
    """
    Create and send the rocket track directly to the API
    
    Args:
        api_url: Base URL of the API
    """
    print("\n" + "="*60)
    print("CREATING ROCKET TRACK")
    print("="*60)
    
    # Create the rocket track
    # From: Lat 32.270878, Lng 36.018677
    # To:   Lat 32.245329, Lng 35.529785
    rocket_track = create_rocket_track_simulation(
        start_lat=32.270878,
        start_lon=36.018677,
        end_lat=32.245329,
        end_lon=35.529785,
        offset_seconds=1
    )
    
    print(f"✅ Rocket track created:")
    print(f"   ID: {rocket_track['_id']}")
    print(f"   Type: {rocket_track['object_type']}")
    print(f"   Points: {len(rocket_track['points'])}")
    print(f"   Speed: {rocket_track['avg_speed']} knots")
    print(f"   From: {rocket_track['starting_point']}")
    print(f"   To: {rocket_track['ending_point']}")
    
    print("\n" + "="*60)
    print("SENDING ROCKET TRACK TO API")
    print("="*60)
    
    try:
        # Use simulator to send the rocket object
        sim = ObjectSimulator([convert_timestamps(rocket_track)])
        sim.run()
        
        print(f"✅ Rocket attack sent successfully!")
        print(f"   Classification: rocket")
        
    except Exception as e:
        print(f"❌ Error sending rocket track: {e}")
        return False
    
    return True


def main():
    """
    Main function to trigger the rocket attack
    """
    print("\n" + "🚀"*30)
    print("ROCKET ATTACK TRIGGER")
    print("🚀"*30)
    
    print("\nThis script will:")
    print("  1. Create a rocket trajectory")
    print("  2. Send the rocket track to the API")
    print("  3. Classify it as a rocket")
    print("\nFrom: Lat 32.270878, Lng 36.018677")
    print("To:   Lat 32.245329, Lng 35.529785")
    print("\nMake sure your API is running on http://localhost:3001")
    print("\n" + "="*60)
    
    # Send rocket track
    success = send_rocket_track_to_api()
    
    # Final summary
    print("\n" + "="*60)
    if success:
        print("✅ ROCKET ATTACK TRIGGERED SUCCESSFULLY!")
    else:
        print("⚠️  ROCKET ATTACK FAILED")
    print("="*60)
    
    print("\nCheck your radar display for the rocket threat!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()



