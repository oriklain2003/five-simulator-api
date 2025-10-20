"""
Script to send random radar points within a polygon
Sends 10 random points every 10 seconds
"""
import requests
import random
import time
from datetime import datetime

from config import API_BASE_URL

# Polygon boundaries
# POLYGON ((33.00293 29.190533, 37.265625 29.190533, 37.265625 33.504759, 33.00293 33.504759, 33.00293 29.190533))
POLYGON_BOUNDS = {
    "min_lon": 35.249634,
    "max_lon": 35.966492,
    "min_lat": 33.114549,
    "max_lat": 33.911454
}

API_URL = API_BASE_URL
RADAR_ENDPOINT = "/objects/radar-point"


def generate_random_point():
    """Generate a random point within the polygon bounds"""
    lat = random.uniform(POLYGON_BOUNDS["min_lat"], POLYGON_BOUNDS["max_lat"])
    lon = random.uniform(POLYGON_BOUNDS["min_lon"], POLYGON_BOUNDS["max_lon"])
    alt = random.uniform(1000, 10000)  # Random altitude between 1000-10000 ft
    
    return {
        "lat": lat,
        "lon": lon,
        "alt": alt
    }


def send_radar_point(point):
    """Send a radar point to the API"""
    payload = {
        "lng": point["lon"],
        "lat": point["lat"],
        "alt": point["alt"]
    }
    
    try:
        response = requests.post(f"{API_URL}{RADAR_ENDPOINT}", json=payload)
        response.raise_for_status()
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✓ Sent radar point: lat={point['lat']:.6f}, lon={point['lon']:.6f}, alt={point['alt']:.0f}ft")
        return True
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✗ Error sending radar point: {e}")
        return False


def send_batch_of_points(num_points=50):
    """Send a batch of random radar points"""
    print(f"\n{'='*70}")
    print(f"Sending batch of {num_points} random radar points...")
    print(f"{'='*70}")
    
    success_count = 0
    for i in range(num_points):
        point = generate_random_point()
        if send_radar_point(point):
            success_count += 1
        time.sleep(0.1)  # Small delay between points in the same batch
    
    print(f"{'='*70}")
    print(f"Batch complete: {success_count}/{num_points} points sent successfully")
    print(f"{'='*70}\n")


def main():
    """Main loop to continuously send radar points every 10 seconds"""
    print("="*70)
    print("RANDOM RADAR POINT GENERATOR")
    print("="*70)
    print(f"\nPolygon boundaries:")
    print(f"  Longitude: {POLYGON_BOUNDS['min_lon']} to {POLYGON_BOUNDS['max_lon']}")
    print(f"  Latitude:  {POLYGON_BOUNDS['min_lat']} to {POLYGON_BOUNDS['max_lat']}")
    print(f"\nSending 10 random points every 10 seconds")
    print(f"API endpoint: {API_URL}{RADAR_ENDPOINT}")
    print(f"\nPress Ctrl+C to stop")
    print("="*70)
    
    batch_number = 1
    
    try:
        while True:
            print(f"\n>>> Batch #{batch_number}")
            send_batch_of_points(num_points=50)
            
            print(f"Waiting 10 seconds before next batch...")
            time.sleep(10)
            
            batch_number += 1
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Stopped by user")
        print(f"Total batches sent: {batch_number - 1}")
        print("="*70)


if __name__ == "__main__":
    main()

