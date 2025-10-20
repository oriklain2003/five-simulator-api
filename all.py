import math
import random
import time
import uuid
import datetime
import json


# Define radars with their positions and ranges
RADARS = [
    {
        "name": "north",
        "lat": 32.916485,
        "lng": 35.354004,
        "range": 250000  # 250km in meters
    },
    {
        "name": "center",
        "lat": 32.157012,
        "lng": 34.870605,
        "range": 250000
    },
    {
        "name": "south",
        "lat": 30.642638,
        "lng": 34.942017,
        "range": 250000
    }
]


# Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Bearing between points
def bearing(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


# Move point
def move_point(lat, lon, speed, brg, dt=1):
    R = 6371000
    distance = speed * dt
    brg = math.radians(brg)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) + math.cos(lat1) * math.sin(distance / R) * math.cos(brg))
    lon2 = lon1 + math.atan2(math.sin(brg) * math.sin(distance / R) * math.cos(lat1),
                             math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


# Check which radars detect a point
def get_detecting_radars(lat, lon):
    """
    Returns list of radars that can detect the given position
    """
    detecting_radars = []
    for radar in RADARS:
        distance = haversine(lat, lon, radar["lat"], radar["lng"])
        distance_km = distance / 1000
        if distance <= radar["range"]:
            detecting_radars.append(radar)
            print(f"    ✓ Radar '{radar['name']}' can detect: {distance_km:.1f}km (within {radar['range']/1000}km range)")
        else:
            print(f"    ✗ Radar '{radar['name']}' out of range: {distance_km:.1f}km (max {radar['range']/1000}km)")
    return detecting_radars


# Add random deviation to a point (backward from direction of travel)
def add_position_deviation(lat, lon, bearing, radar_index, total_radars, max_deviation_meters=100):
    """
    Add random deviation to a position (simulates radar detection uncertainty)
    The deviation is behind the actual position (opposite to direction of travel)
    Later radars (higher index) are closer to the actual position
    
    Args:
        lat: latitude of the point
        lon: longitude of the point
        bearing: direction of travel in degrees
        radar_index: index of this radar (0 = first, will be furthest behind)
        total_radars: total number of radars detecting this point
        max_deviation_meters: maximum deviation in meters (default 100m)
    """
    # Calculate backward distance based on radar index
    # First radar (index 0) is furthest behind, last radar is closest
    # Distance range: 30m to 150m behind
    min_behind_distance = 30
    max_behind_distance = 150
    
    # Calculate how far behind this detection should be
    # radar_index 0 (first) = furthest behind
    # radar_index (total_radars-1) (last) = closest
    if total_radars > 1:
        # Linear interpolation from max to min
        behind_factor = 1.0 - (radar_index / (total_radars - 1))
    else:
        behind_factor = 0.5  # Single radar, middle distance
    
    behind_distance = min_behind_distance + (max_behind_distance - min_behind_distance) * behind_factor
    
    # Add some random variation to the behind distance (±10%)
    behind_distance *= random.uniform(0.9, 1.1)
    
    # Calculate perpendicular deviation (left/right from direction)
    perpendicular_deviation = random.uniform(-max_deviation_meters, max_deviation_meters)
    
    # Backward angle (opposite to bearing)
    backward_bearing = (bearing + 180) % 360
    
    # Move backward first
    temp_lat, temp_lon = move_point(lat, lon, behind_distance, backward_bearing, dt=1)
    
    # Then move perpendicular (left or right)
    perpendicular_bearing = (bearing + 90) % 360 if perpendicular_deviation > 0 else (bearing - 90) % 360
    final_lat, final_lon = move_point(temp_lat, temp_lon, abs(perpendicular_deviation), perpendicular_bearing, dt=1)
    
    return final_lat, final_lon


# Generate radar detection points for a given point
def generate_radar_detections(point, point_idx):
    """
    Generate radar detection points for a given point.
    Returns a list of detection points, one for each detecting radar.
    If multiple radars detect it, adds 0.5s delay between detections.
    Detection points are positioned behind the actual position (opposite to direction of travel).
    Later detections (higher timestamp) are closer to the actual position.
    """
    detecting_radars = get_detecting_radars(point["lat"], point["lon"])
    
    if not detecting_radars:
        return []  # No radar detects this point
    
    detection_points = []
    base_timestamp = datetime.datetime.fromisoformat(point["timestamp"].replace("+00:00", ""))
    bearing = point.get("bearing", 0)  # Get direction of travel
    total_radars = len(detecting_radars)
    
    for i, radar in enumerate(detecting_radars):
        # Add time offset: 0s for first radar, 0.5s for each additional radar
        time_offset = i * 0.5
        detection_time = base_timestamp + datetime.timedelta(seconds=time_offset)
        
        # Add deviation behind the actual position
        # First radar (i=0) is furthest behind, last radar is closest
        deviated_lat, deviated_lon = add_position_deviation(
            point["lat"], 
            point["lon"], 
            bearing, 
            i, 
            total_radars
        )
        
        detection_point = {
            "timestamp": detection_time.isoformat() + "+00:00",
            "lat": deviated_lat,
            "lon": deviated_lon,
            "altitude": point["altitude"],
            "speed_kts": point["speed_kts"],
            "bearing": point["bearing"],
            "rotation": point.get("rotation", point["bearing"] - 90),  # Use rotation from original point
            "point_id": f"{point['point_id']}_radar_{radar['name']}",
            "detected_by_radar": radar["name"],
            "original_lat": point["lat"],
            "original_lon": point["lon"]
        }
        detection_points.append(detection_point)
        print(f"      → Created detection point for radar '{radar['name']}' at +{time_offset}s")
    
    return detection_points


# Aircraft simulator
def simulate_aircraft(start, end, min_speed_kts, max_speed_kts, min_alt_ft, max_alt_ft, object_type, color,
                      behavior="normal", name=None):
    cruise_speed_kts = random.uniform(min_speed_kts, max_speed_kts)
    cruise_speed = cruise_speed_kts * 0.514444
    altitude = random.uniform(min_alt_ft, max_alt_ft)
    total_distance = haversine(start['lat'], start['lon'], end['lat'], end['lon'])

    # Initial logging
    print(f"\n{'='*60}")
    print(f"Simulating {object_type.upper()} ({behavior})")
    print(f"Start: lat={start['lat']:.6f}, lon={start['lon']:.6f}")
    print(f"End:   lat={end['lat']:.6f}, lon={end['lon']:.6f}")
    print(f"Total distance: {total_distance:.2f} meters ({total_distance/1000:.2f} km)")
    print(f"Speed: {cruise_speed_kts:.2f} knots ({cruise_speed:.2f} m/s)")
    print(f"Altitude: {altitude:.2f} feet")
    print(f"{'='*60}")

    points = []
    timestamp = datetime.datetime.utcnow()
    current_lat, current_lon = start['lat'], start['lon']
    prev_bearing, prev_speed = None, None
    total_dir_changes, total_speed_changes, total_alt_changes = 0, 0, 0
    point_idx = 0
    d= 0
    while haversine(current_lat, current_lon, end['lat'], end['lon']) > cruise_speed and d < 100:
        brg = bearing(current_lat, current_lon, end['lat'], end['lon'])

        # Behavior adjustments
        if object_type == "bird":
            # dynamic altitude
            altitude += random.uniform(-200, 200)
            if altitude < 0: altitude = 0
        elif object_type == "helicopter":
            # slight altitude variation
            altitude += random.uniform(-50, 50)
            altitude = max(100, min(altitude, max_alt_ft))
        elif object_type == "jet" and behavior == "aggressive":
            # strong random turns, speed, altitude changes
            brg += random.uniform(-45, 45)
            cruise_speed_kts += random.uniform(-50, 50)
            cruise_speed_kts = max(min_speed_kts, min(cruise_speed_kts, max_speed_kts))
            cruise_speed = cruise_speed_kts * 0.514444
            altitude += random.uniform(-500, 500)
            altitude = max(min_alt_ft, min(altitude, max_alt_ft))
        # else: drone, rocket, plane, jet chill -> straight, constant

        current_lat, current_lon = move_point(current_lat, current_lon, cruise_speed, brg, dt=10)

        # Track stats
        if prev_bearing is not None:
            d = abs(brg - prev_bearing)
            if d > 180: d = 360 - d
            total_dir_changes += d
        if prev_speed is not None:
            total_speed_changes += abs(cruise_speed_kts - prev_speed)
        if points:
            total_alt_changes += abs(altitude - points[-1]['altitude'])

        # Calculate remaining distance
        remaining_distance = haversine(current_lat, current_lon, end['lat'], end['lon'])
        
        # Log every point
        print(f"Point {point_idx}: lat={current_lat:.6f}, lon={current_lon:.6f}, "
              f"alt={altitude:.0f}ft, speed={cruise_speed_kts:.1f}kts, "
              f"bearing={brg:.1f}°, remaining={remaining_distance:.0f}m")

        # Calculate rotation (bearing - 90 for correct orientation)
        rotation = brg - 90
        
        points.append({
            "timestamp": timestamp.isoformat() + "+00:00",
            "lat": current_lat,
            "lon": current_lon,
            "altitude": altitude,
            "speed_kts": cruise_speed_kts,
            "bearing": brg,
            "rotation": rotation,
            "point_id": f"p{point_idx}"
        })

        prev_bearing = brg
        prev_speed = cruise_speed_kts
        timestamp += datetime.timedelta(seconds=10)
        point_idx += 1

    # Generate radar detection points for each original point
    print(f"\nGenerating radar detections...")
    all_points_with_radar = []
    total_detections = 0
    
    for point in points[:100]:  # Only process first 100 points
        # Add the original point
        all_points_with_radar.append(point)
        
        # Generate and add radar detection points
        print(f"\n  Processing Point {point['point_id']} at lat={point['lat']:.4f}, lon={point['lon']:.4f}:")
        detections = generate_radar_detections(point, point["point_id"])
        all_points_with_radar.extend(detections)
        if detections:
            total_detections += len(detections)
            radar_names = [d["detected_by_radar"] for d in detections]
            print(f"  ✓ Generated {len(detections)} detection(s) from radar(s): {', '.join(radar_names)}")
        else:
            print(f"  ✗ No radar detections for this point")
    
    # Sort all points by timestamp to maintain chronological order
    all_points_with_radar.sort(key=lambda p: p["timestamp"])
    
    # Summary logging
    print(f"\n{'*'*60}")
    print(f"✓ Simulation complete for {object_type.upper()}")
    print(f"Total original points: {len(points)}")
    print(f"Total radar detections: {total_detections}")
    print(f"Total points (original + radar): {len(all_points_with_radar)}")
    print(f"Total time: {len(points) * 10} seconds ({len(points) * 10 / 60:.1f} minutes)")
    print(f"Points used (max 100): {min(len(points), 100)}")
    print(f"Total direction changes: {total_dir_changes:.1f}°")
    print(f"Total speed changes: {total_speed_changes:.1f} knots")
    print(f"Total altitude changes: {total_alt_changes:.1f} feet")
    print(f"{'*'*60}\n")

    result = {
        "_id": str(uuid.uuid4()),
        "object_type": object_type,
        "color_on_map": color,
        "created_at": datetime.datetime.utcnow().isoformat() + "+00:00",
        "updated_at": datetime.datetime.utcnow().isoformat() + "+00:00",
        "avg_speed": cruise_speed_kts,
        "altitude": altitude,
        "starting_point": start,
        "ending_point": end,
        "total_distance": int(total_distance),
        "total_distance_simulated": int(total_distance),
        "total_direction_changes": int(total_dir_changes),
        "total_speed_changes": int(total_speed_changes),
        "total_altitude_changes": int(total_alt_changes),
        "points": all_points_with_radar,  # Now includes both original and radar detection points
        "type":"arrow"
    }
    
    # Add name if provided
    if name:
        result["name"] = name
    
    return result


import firebase_admin
from firebase_admin import credentials, firestore
import os
import json


# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:  # avoid re-initialization
        with open("firebase.json") as f:
            service_account = json.load(f)
        cred = credentials.Certificate(service_account)

        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")


# Get Firestore client
def get_db():
    if not firebase_admin._apps:
        raise Exception("Firebase not initialized. Call initialize_firebase() first.")
    return firestore.client()


# Push a document to Firestore
def create_course(course_data, processed_points):
    db = get_db()

    # Add course document
    course_ref = db.collection("courses").add(course_data)[1]  # returns (update_time, ref)
    print(f"Created course with ID: {course_ref.id}")

    # Add points to subcollection using batch
    batch = db.batch()
    for point in processed_points:
        point_ref = db.collection("courses").document(course_ref.id).collection("points").document(point["point_id"])
        batch.set(point_ref, point)
    batch.commit()
    print(f"Added {len(processed_points)} points to course {course_ref.id}")

    return {
        "id": course_ref.id,
        **course_data,
        "points": processed_points
    }


def send_radar_points_with_timing(api_url):
    """
    Send radar points with proper timing: first at 10s, then +1s for each subsequent
    Returns the positions for later use in the moving object simulation
    """
    import requests
    
    positions = [
        {"lat": 33.261657, "lon": 35.419922, "alt": 5000},
        {"lat": 33.251321, "lon": 35.427132, "alt": 5000},
        {"lat": 33.244143, "lon": 35.413399, "alt": 5000},
        {"lat": 33.233519, "lon": 35.429878, "alt": 5000}
    ]
    
    print("Starting radar point transmission...")
    
    # First point after 10 seconds
    print("Waiting 10 seconds before sending first radar point...")
    # time.sleep(10)
    
    for i, pos in enumerate(positions):
        payload = {
            "lng": pos["lon"],
            "lat": pos["lat"],
            "alt": pos["alt"]
        }
        
        try:
            response = requests.post(f"{api_url}/objects/radar-point", json=payload)
            print(response)
            print(f"Sent radar point {i+1}/4: lat={pos['lat']:.4f}, lon={pos['lon']:.4f}, alt={pos['alt']}")
            
            # Wait 1 second before next point (except after the last one)
            if i < len(positions) - 1:
                time.sleep(1)
        except Exception as e:
            print(f"Error sending radar point {i+1}: {e}")
    
    print("All radar points sent!")
    return positions


def create_drone_track_simulation(offset_seconds=14):
    """
    Create a moving unknown object that will be tracked and later classified as a drone
    This appears 1 second after the last radar point (T+14s)
    
    Args:
        offset_seconds: Seconds to offset the timestamps (14s = after radar attack at T+10,11,12,13s)
    """
    # Start from the last radar point position and move towards Israel
    start_position = {"lat": 33.236677, "lon": 35.430565}
    # start_position = {"lat":33.172175, "lon": 35.427475}

    end_position = {"lat": 33.038601, "lon": 35.437775}  # Moving south towards Israel
    
    # Create the flight simulation
    flight_data = simulate_aircraft(
        start_position, 
        end_position, 
        80, 80,  # speed: 80 kts
        5000, 5000,  # altitude: 5000 ft
        "arrow",
        "#40E0D0",
        "normal",
        "ב149"  # Name: Suspicious drone
    )
    
    # Offset all timestamps by 14 seconds so drone appears at T+14s (1s after last radar point)
    base_time = datetime.datetime.utcnow()
    offset_time = base_time + datetime.timedelta(seconds=offset_seconds)
    
    # Update all point timestamps
    for point in flight_data["points"]:
        original_time = datetime.datetime.fromisoformat(point["timestamp"].replace("+00:00", ""))
        time_diff = original_time - base_time
        new_time = offset_time + time_diff
        point["timestamp"] = new_time.isoformat() + "+00:00"
    
    # Generate radar detections for the drone track and merge with original points
    print(f"\nGenerating radar detections for drone track...")
    all_points_with_radar = []
    total_radar_detections = 0
    
    for point in flight_data["points"]:
        # Add original point
        all_points_with_radar.append(point)
        
        # Add radar detection points
        detections = generate_radar_detections(point, point["point_id"])
        all_points_with_radar.extend(detections)
        total_radar_detections += len(detections)
    
    # Sort all points by timestamp
    all_points_with_radar.sort(key=lambda p: p["timestamp"])
    
    # Replace points array with merged and sorted points
    flight_data["points"] = all_points_with_radar
    print(f"Generated {total_radar_detections} radar detection points for drone track")
    print(f"Total points (original + radar): {len(all_points_with_radar)}")
    
    # Update creation timestamps
    flight_data["created_at"] = offset_time.isoformat() + "+00:00"
    flight_data["updated_at"] = offset_time.isoformat() + "+00:00"
    flight_data["detailedMessage"] = "נתוני התקדמות זהים לריצה שזוהתה לפני כ-10 דקות,ו-5 דקות"
    # Use a specific ID so it can be tracked
    flight_data["_id"] = "b83e5878-d87b-4c03-8c6e-abca85bf1236"
    flight_data["type"] = "arrow"
    flight_data["steps"] = [
        {
            "question": "האם תרצה שאקריא בד\"ח פעולה?",
            "answers": ["""
1.העלה כוננות לכיפת ברזל ופטריוט.
2.זנק את צוות היירוט.
3.זנק מטוסי קרב מרמת דוד.
4.זנק מסוקי קרב מרמת דוד.
5.פנה את המרחב האווירי.
6.בצע מסדר זיהוי.
7.כנס את תא השליטה
"""
            ]
        },
        {
            "question": "האם תרצה שאציג לך זמן אחרון להחלטה?",
            "answers": [
                "120 שניות לחציית קו גבול לישראל"
            ]
        },
        {
            "question": "האם תרצה שאבנה מכרז אש?",
            "answers": [
                "95 אחוז פגיעה לכיפת ברזל",
                "80 אחוז פגיעה לטיל פטריוט",
                "20 אחוז לפגיעה של טיל ממטוס קרב"
            ]
        }
    ]
    flight_data["steps"].extend([
                {
                    "question": "מתי ואיך אני נדרש לפעול על הכטבם",
                    "answers": [
                        "יש לפעול מיידית על המטרה כאשר ההחלטה לסווג אותה ככטב\"ם אויב",
                        "כרוז צוות ליירוט",
                        "זנק מסוקי קרב",
                        "זנק מטוסי קרב",
                        "העלה כוננות לסוללות הטילים",
                        "העלה מעגל שליטה",
                        "העלה חומסי gps"
                    ]
                },
                {
                    "question": "מה הסמכויות שלי להפלת הכטבם",
                    "answers": [
                        "הינך ראשי להפיל את הכטב\"ם בחציית קו גבול בהיעדר קשר עם השולט"
                    ]
                },
                {
                    "question": "למה זיהית את המטרה ככטבם",
                    "answers": [
                        "מטרה ב149 התגלתה במיקום שממנו בתגלו וסווגו כטבמים",
                        "בשבועיים האחרונים התגלו וסווגו באזור זה 5 כטב\"מים, אחד מהם יורט ע\"י כיפת ברזל",
                        "פרופיל טיסה תואם לקטב\"ם 5 אלף רגל ו80 קשר, כיוון הטיסה מאיים, בנתיב התכנסות למדינה"
                    ]
                },
                {
                    "question": "למה אתה ממליץ לסווג אותה ככטבם",
                    "answers": [
                        "מטרה ב149 התגלתה במיקום שממנו בתגלו וסווגו כטבמים",
                        "בשבועיים האחרונים התגלו וסווגו באזור זה 5 כטב\"מים, אחד מהם יורט ע\"י כיפת ברזל",
                        "פרופיל טיסה תואם לקטב\"ם 5 אלף רגל ו80 קשר, כיוון הטיסה מאיים, בנתיב התכנסות למדינה"
                    ]
                }
            ])
    flight_data["should_classify"] = True  # Flag for classification
    flight_data["originCountry"] = "בדרום לבנון"
    flight_data["moving_to"] = "צפון המדינה"
    flight_data["classification_info"] = {
        "suggested_identification": "drone",
        "suggestion_reason": """המטרה התגלתה באזור שיצאו ממנו 5 כטבמים בשבוע האחרון

מהירות וגובה התואמת לכטבם מסוג שהד

כיוון התקדמות מאיים לשטח רגיש / אוכלוסייה

לא טס בפרופיל של ציפורים

90 אחוז וודאי"""
    }
    
    return flight_data

# Example usage
if __name__ == "__main__":

    start_point = {"lat": 31.1444067, "lon": 35.1205757}
    end_point = {"lat": 31.1464498, "lon": 35.0939402}
    birds_start_points = [
        {"lat": 33.865895211796346, "lon": 35.84838867187501},
        {"lat": 33.92885480180959, "lon": 35.74951171875001},
        {"lat": 33.01273389791075, "lon": 35.62866210937501},
        {"lat": 33.282488692700504, "lon": 35.73852539062501},
        {"lat": 33.10584293285769, "lon": 36.07360839843751},
        {"lat": 33.89621446335144, "lon": 36.24938964843751},
        {"lat": 33.008075959291055, "lon": 35.96923828125001},
        {"lat": 33.175612478499346, "lon": 35.86486816406251},
        {"lat": 33.519026027827515, "lon": 36.08459472656251},
        {"lat": 33.579220642875676, "lon": 36.50756835937501},
        {"lat": 33.43561304116276, "lon": 36.96350097656251},
        {"lat": 33.34284135639302, "lon": 36.66687011718751},
        {"lat": 33.040676557717454, "lon": 36.57897949218751},
        {"lat": 33.175612478499346, "lon": 36.12854003906251},
        {"lat": 33.38460040620993, "lon": 36.00769042968751},
        {"lat": 33.26855544621476, "lon": 36.33178710937501},
        {"lat": 33.4031537914036, "lon": 36.18347167968751},
        {"lat": 33.713355353177555, "lon": 36.30981445312501},
        {"lat": 33.8334428466495, "lon": 36.82067871093751},
        {"lat": 33.708733368521614, "lon": 37.00744628906251},
        {"lat": 33.602361666817515, "lon": 36.76025390625001},
        {"lat": 33.217448573031035, "lon": 36.87561035156251},
        {"lat": 33.863562548378965, "lon": 36.62292480468751},
        {"lat": 33.810361684869015, "lon": 36.39221191406251},
        {"lat": 33.063924198120645, "lon": 36.89208984375001}]
    birds_end_point = {"lat": 31.1464498, "lon": 35.0939402}
    data = {"bird": [], "plane": [], "jet": []}
    for bird_start_point in birds_start_points:
        data["bird"].append(simulate_aircraft(bird_start_point, birds_end_point, 30, 70, 1000, 6000, "bird", "orange"))

    planes_points: list[tuple] = [
        ({"lat": 32.35676318267811, "lon": 33.72802734375001}, {"lat": 31.961483557268558, "lon": 34.45312500000001}, {"speed":350, "alt":280000, "name":"ELY358"}),
        ({"lat": 33.78371305547283, "lon": 34.65637207031251}, {"lat": 34.043556504127444, "lon": 34.10705566406251}, {"speed":400, "alt":370000, "name":"TKJ318"}),
        ({"lat": 32.0383483283312, "lon": 33.64013671875001}, {"lat": 31.742182762117984, "lon": 34.15649414062501}, {"speed":350, "alt":380000, "name":"ACA56"}),
        ({"lat": 33.906895551288684, "lon": 35.61767578125001}, {"lat": 33.73804486328907, "lon": 35.28808593750001}, {"speed":250, "alt":80000, "name":"DST445"}),
        ({"lat": 33.63291573870479, "lon": 35.29083251953126}, {"lat": 33.46810795527896, "lon": 35.13153076171876}, {"speed":250, "alt":60000, "name":"KGK456"}),
        ({"lat": 33.9388027508458, "lon": 34.71130371093751}, {"lat": 33.95247360616284, "lon": 35.11779785156251}, {"speed":300, "alt":100000, "name":"DHX160"}),
        ({"lat": 32.32891738775126, "lon": 34.51354980468751}, {"lat": 32.537551746769, "lon": 33.86535644531251}, {"speed":350, "alt":280000, "name":"ELY337"}),
        ({"lat": 33.957030069982316, "lon": 36.40869140625001}, {"lat": 33.84760762988741, "lon": 36.55151367187501}, {"speed":400, "alt":370000, "name":"RED165"}),
        ({"lat": 33.678639851675555, "lon": 36.79870605468751}, {"lat": 33.6008944080788, "lon": 36.85913085937501}, {"speed":400, "alt":370000, "name":"YEL897"})
    ]

    for start_point_plane, end_point_plane, plane_data in planes_points:
        data["plane"].append(
            simulate_aircraft(start_point_plane, end_point_plane, plane_data["speed"] - 5, plane_data["speed"] + 5, plane_data["alt"] - 300, plane_data["alt"] + 300, "plane", "white", "normal", plane_data["name"]))

    jet_chill_points: list[tuple] = [
        ({"lat": 32.784965481461185, "lon": 35.40206909179688}, {"lat": 32.81844077366436, "lon": 33.31005859375001}, {"speed":350, "alt":150000, "name":"ציוני1"}),
        ({"lat": 32.765336175015776, "lon": 35.37048339843751}, {"lat": 32.79651010951669, "lon": 33.26748657226563},{"speed":350, "alt":140000, "name":"ציוני2"}),
        ({"lat": 32.87036022808352, "lon": 34.56298828125001}, {"lat": 31.100745405144245, "lon": 34.59045410156251},{"speed":400, "alt":210000, "name":"ברדלס1"}),
        ({"lat": 32.91187391621322, "lon": 34.35974121093751}, {"lat": 31.215712251730736, "lon": 34.34326171875001},{"speed":400, "alt":180000, "name":"ברדלס2"}),
        ({"lat": 32.27900558170509, "lon": 35.49682617187501}, {"lat": 35.362563311220384, "lon": 35.50781250000001},{"speed":450, "alt":300000, "name":"אס1"}),
        ({"lat": 32.299902241069326, "lon": 35.45562744140626},{"lat": 35.400834826722196, "lon": 35.46936035156251},{"speed":450, "alt":300000, "name":"אס2"})
    ]
    i = 0
    for start_point_jet_chill, end_point_jet_chill, jet_data in jet_chill_points:
        i += 1
        if i < 2:
            data["jet"].append(
                simulate_aircraft(start_point_jet_chill, end_point_jet_chill, jet_data["speed"] - 5, jet_data["speed"] + 5, jet_data["alt"] - 300, jet_data["alt"] + 300, "jet", "yellow",
                                  "chill", jet_data["name"]))
        else:
            data["jet"].append(
                simulate_aircraft(start_point_jet_chill, end_point_jet_chill, jet_data["speed"] - 5, jet_data["speed"] + 5, jet_data["alt"] - 300, jet_data["alt"] + 300, "jet", "yellow",
                                  "aggressive", jet_data["name"]))


    all = data["bird"]
    all.extend(data["jet"])
    all.extend(data["plane"])
    

    with open("../simulated_flights7.json", 'w') as www:
        json.dump(all, www)
    
    print("\n" + "="*60)
    print("Simulation data prepared and saved!")
    print("="*60)
    for course_type in data:
        for course in data[course_type]:
            points = course.pop("points")
            create_course(course, points)

    print(json.dumps(data, indent=2))
