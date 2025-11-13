"""
Realtime flight simulator using FlightRadar24 API
Fetches live flight data and sends it to the API
"""
import os
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any
import config

from fr24sdk.client import Client
from fr24sdk.models.geographic import Boundary



# Boundaries
MIN_LAT = 29.53523
MAX_LAT = 33.614619
MIN_LON = 34.145508
MAX_LON = 36.386719


# FlightRadar24 API Token
FR24_API_TOKEN = "019a7948-61c3-72d5-9442-a62e4fea2bef|khA5LNvXdamyXIloiFGiOXkrdgvaB0iZf7sYQwcL33b49ed1"

# Track active flights
active_flights = {}


def fetch_flightradar24_data():
    """Fetch flight data from FlightRadar24 API within boundaries"""
    try:
        # Initialize SDK client with API token
        with Client(api_token=FR24_API_TOKEN) as client:
            # Define bounding box using Boundary model
            # Boundary format: north, south, west, east
            boundary = Boundary(
                north=MAX_LAT,
                south=MIN_LAT,
                west=MIN_LON,
                east=MAX_LON
            )
            
            # Fetch live flight positions within bounds
            response = client.live.flight_positions.get_full(bounds=boundary, altitude_ranges=["1000-50000"])
            
            # Extract flight data from response
            if response and hasattr(response, 'data'):
                return response.data if response.data else []
            return []
    except Exception as e:
        print(f"Error fetching FlightRadar24 data: {e}")
        import traceback
        traceback.print_exc()
        return []


def convert_fr24_to_object(flight):
    """
    Convert FlightRadar24 SDK flight object to our object format
    
    fr24sdk FlightPositionLight attributes:
    - fr24_id: unique flight ID
    - lat: latitude
    - lon: longitude
    - alt: altitude in feet
    - spd: speed in knots
    - hdg: heading/track in degrees
    - callsign: flight callsign
    - reg: aircraft registration
    - origin: origin airport
    - dest: destination airport
    - type: aircraft type code
    - on_ground: on ground status
    """
    try:
        # Skip if no position data
        if not hasattr(flight, 'lat') or not hasattr(flight, 'lon'):
            return None
        
        if flight.lat is None or flight.lon is None:
            return None
        
        # Extract data with defaults
        flight_id = getattr(flight, 'fr24_id', None) or getattr(flight, 'id', None) or f"fr24_{id(flight)}"
        latitude = flight.lat
        longitude = flight.lon
        altitude = getattr(flight, 'alt', 0) or 0  # Already in feet
        speed = getattr(flight, 'gspeed', 0) or 0  # Already in knots
        heading = getattr(flight, 'track', 0) or 0
        heading = heading - 90
        callsign = getattr(flight, 'callsign', '') or ''
        registration = getattr(flight, 'reg', '') or ''
        origin = getattr(flight, 'origin', '') or ''
        destination = getattr(flight, 'dest', '') or ''
        aircraft_type = getattr(flight, 'type', '') or ''
        on_ground = getattr(flight, 'on_ground', 0) == 1
        
        # Create timestamp
        timestamp = datetime.now(timezone.utc)
        
        # Create point
        point = {
            "lat": latitude,
            "lon": longitude,
            "altitude": altitude,
            "timestamp": timestamp,
            "rotation": heading
        }
        
        # Create object
        obj = {
            "_id": f"fr24_{flight_id}",
            "name": callsign.strip() if callsign else (registration or flight_id),
            "object_type": "plane",
            "color_on_map": "#00BFFF",
            "avg_speed": speed,
            "registration": registration,
            "aircraft_type": aircraft_type,
            "origin": origin,
            "destination": destination,
            "on_ground": on_ground,
            "points": [point],
            "ending_point": {
                "lat": latitude,
                "lon": longitude
            }
        }
        
        return obj
    except Exception as e:
        print(f"Error converting flight: {e}")
        import traceback
        traceback.print_exc()
        return None


def transform_to_api_schema(obj):
    """Transform object to API schema"""
    from simulator import ObjectSimulator
    return ObjectSimulator.transform_to_schema(obj)


def send_to_api(object_data):
    """Send object to the API"""
    url = f"{config.API_BASE_URL}{config.OBJECTS_ENDPOINT}"
    
    try:
        response = requests.post(url, json=object_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending to API: {e}")
        return False


def mark_as_deleted(object_id):
    return
    """Mark an object as deleted"""
    url = f"{config.API_BASE_URL}{config.OBJECTS_ENDPOINT}"
    
    payload = {
        'object_id': object_id,
        'is_delete': True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"  [DELETED] Object {object_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error marking as deleted: {e}")
        return False


def update_flight(flight_id, obj):
    """Update or add a flight to active flights"""
    if flight_id in active_flights:
        # Append new point to existing flight
        active_flights[flight_id]['points'].append(obj['points'][0])
        active_flights[flight_id]['ending_point'] = obj['ending_point']
        active_flights[flight_id]['avg_speed'] = obj['avg_speed']
    else:
        # New flight
        active_flights[flight_id] = obj
    
    active_flights[flight_id]['last_seen'] = time.time()


def run_realtime_simulation(running_flag):
    """Main loop for realtime simulation"""
    print("="*70)
    print("REALTIME FLIGHTRADAR24 SIMULATOR")
    print("="*70)
    print(f"Boundaries:")
    print(f"  Latitude:  {MIN_LAT} to {MAX_LAT}")
    print(f"  Longitude: {MIN_LON} to {MAX_LON}")
    print(f"API endpoint: {config.API_BASE_URL}{config.OBJECTS_ENDPOINT}")
    print("="*70)
    
    if Client is None:
        print("ERROR: FlightRadar24 SDK not installed. Run: pip install fr24sdk")
        return
    
    update_count = 0
    
    while running_flag.get('realtime_opensky', False):
        update_count += 1
        print(f"\n>>> Update #{update_count} [{datetime.now().strftime('%H:%M:%S')}]")
        
        # Fetch data from FlightRadar24
        flights = fetch_flightradar24_data()
        
        if not flights:
            print("No flights in the area")
        else:
            print(f"Found {len(flights)} flights")
            
            current_flight_ids = set()
            
            # Process each flight
            for flight in flights:
                obj = convert_fr24_to_object(flight)
                if obj:
                    flight_id = obj['_id']
                    current_flight_ids.add(flight_id)
                    
                    # Update flight data
                    update_flight(flight_id, obj)
                    
                    # Transform and send to API
                    api_data = transform_to_api_schema(active_flights[flight_id])
                    if send_to_api(api_data):
                        points_count = len(active_flights[flight_id]['points'])
                        print(f"  [UPDATED] {obj['name']} - Points: {points_count}")
            
            # Check for flights that disappeared
            disappeared = []
            current_time = time.time()
            for flight_id, flight_data in list(active_flights.items()):
                if flight_id not in current_flight_ids:
                    time_since_seen = current_time - flight_data.get('last_seen', current_time)
                    if time_since_seen > 30:  # 30 seconds timeout
                        disappeared.append(flight_id)
            
            # Mark disappeared flights as deleted
            for flight_id in disappeared:
                object_id = active_flights[flight_id]['_id']
                if mark_as_deleted(object_id):
                    del active_flights[flight_id]
        
        # Wait before next update
        print(f"Waiting 5 seconds before next update...")
        for _ in range(10):
            if not running_flag.get('realtime_opensky', False):
                break
            time.sleep(1)
    
    # Clean up: mark all active flights as deleted
    print("\n\nStopping simulator, cleaning up active flights...")
    for flight_id, flight_data in list(active_flights.items()):
        mark_as_deleted(flight_data['_id'])
    
    active_flights.clear()
    print("Realtime FlightRadar24 simulator stopped")


if __name__ == "__main__":
    running = {'realtime_opensky': True}
    try:
        run_realtime_simulation(running)
    except KeyboardInterrupt:
        print("\nStopped by user")
        running['realtime_opensky'] = False

