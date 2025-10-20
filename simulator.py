"""
Main simulation logic for replaying object updates in real-time
"""
import time
import requests
import math
from datetime import datetime
from typing import List, Dict, Any, Set
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
import config


def convert_timestamps_to_iso(obj):
    """
    Recursively convert DatetimeWithNanoseconds objects to ISO format strings
    
    Args:
        obj: Object that may contain datetime objects
        
    Returns:
        Object with all datetimes converted to ISO strings
    """
    if isinstance(obj, (DatetimeWithNanoseconds, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_timestamps_to_iso(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps_to_iso(item) for item in obj]
    else:
        return obj


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing (rotation) from point 1 to point 2 in degrees.
    
    Args:
        lat1: Latitude of the first point
        lon1: Longitude of the first point
        lat2: Latitude of the second point
        lon2: Longitude of the second point
        
    Returns:
        Bearing in degrees (0-360), where 0 is North, 90 is East, 180 is South, 270 is West
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon_diff_rad = math.radians(lon2 - lon1)

    # Calculate bearing
    x = math.sin(lon_diff_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon_diff_rad)

    bearing_rad = math.atan2(x, y)
    bearing_deg = math.degrees(bearing_rad)

    # Normalize to 0-360
    bearing_deg = (bearing_deg + 360) % 360

    return bearing_deg


class ObjectSimulator:
    def __init__(self, courses: List[Dict[str, Any]]):
        """
        Initialize the simulator with course data
        
        Args:
            courses: List of course objects with their points
        """
        self.courses = courses
        self.all_points = []
        self.start_time = None
        self.current_simulation_time = 0
        self.processed_point_indices = set()
        self.object_states = {}  # Store current state of each object
        self.last_update_time = {}  # Track last update time for each object
        self.classification_sent = set()  # Track which objects have had classification sent

    def prepare_simulation(self):
        """
        Extract all points from all courses and prepare for simulation
        """
        print("Preparing simulation...")

        for course in self.courses:
            object_id = course.get('_id')
            points = course.get('points', [])

            # Initialize object state (empty, will be built up during simulation)
            self.object_states[object_id] = {
                **{k: v for k, v in course.items() if k != 'points'},
                'points': []
            }

            # Add each point to the all_points list with its parent object ID
            for point in points:
                if 'timestamp' in point:
                    self.all_points.append({
                        'object_id': object_id,
                        'point_data': point,
                        'timestamp': point['timestamp']
                    })

        # Sort all points by timestamp
        self.all_points.sort(key=lambda p: p['timestamp'])

        if not self.all_points:
            print("No points found to simulate!")
            return False

        # Set ground zero (first timestamp)
        self.start_time = self.all_points[0]['timestamp']

        print(f"Found {len(self.all_points)} total points across {len(self.courses)} objects")
        print(f"Simulation start time (ground 0): {self.start_time}")
        print(f"Simulation will run for approximately {self._get_total_duration()} seconds")

        return True

    def _get_total_duration(self) -> float:
        """Calculate total simulation duration in seconds"""
        if not self.all_points:
            return 0
        last_time = self.all_points[-1]['timestamp']
        delta = last_time - self.start_time
        return delta.total_seconds()

    def _get_relative_time(self, timestamp) -> float:
        """
        Get relative time in seconds from ground zero
        
        Args:
            timestamp: DatetimeWithNanoseconds object
            
        Returns:
            Seconds since start_time
        """
        delta = timestamp - self.start_time
        return delta.total_seconds()

    def _get_points_to_process(self) -> List[Dict[str, Any]]:
        """
        Get all points that should be processed at current simulation time
        
        Returns:
            List of point data with object IDs
        """
        points_to_add = []

        for idx, point_entry in enumerate(self.all_points):
            if idx in self.processed_point_indices:
                continue

            relative_time = self._get_relative_time(point_entry['timestamp'])

            if relative_time <= self.current_simulation_time:
                points_to_add.append({
                    'index': idx,
                    'object_id': point_entry['object_id'],
                    'point': point_entry['point_data']
                })

        return points_to_add

    def _update_object_state(self, object_id: str, point: Dict[str, Any]):
        """
        Add a point to an object's state
        
        Args:
            object_id: The object ID
            point: The point data to add
        """
        if object_id in self.object_states:
            self.object_states[object_id]['points'].append(point)
            self.last_update_time[object_id] = self.current_simulation_time

    def _send_object_update(self, object_id: str, is_delete: bool = False):
        """
        Send object data to the REST API
        
        Args:
            object_id: The object ID
            is_delete: Whether this is a deletion marker
        """
        url = f"{config.API_BASE_URL}{config.OBJECTS_ENDPOINT}"

        payload = {
            'object_id': object_id,
            'is_delete': is_delete
        }

        if not is_delete:
            # Include full object data
            payload.update(self.object_states[object_id])

        # Transform to schema
        payload_good = self.transform_to_schema(payload)
        
        try:
            # Send the main object update
            response = requests.post(url, json=payload_good)
            response.raise_for_status()

            action = "DELETED" if is_delete else "UPDATED"
            print(f"  [{action}] Object {object_id} - Points: {len(self.object_states[object_id]['points'])}")
            
            # Check if we need to send a classification suggestion (only once on first update)
            if (not is_delete and 
                self.object_states[object_id].get('should_classify') and
                object_id not in self.classification_sent):
                self._send_classification_suggestion(object_id, payload_good, payload)
                self.classification_sent.add(object_id)  # Mark as sent

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to send update for {object_id}: {e}")
    
    def _send_classification_suggestion(self, object_id: str, schema_obj: Dict[str, Any], payload):
        """
        Send a classification suggestion for an object
        
        Args:
            object_id: The object ID
            schema_obj: The transformed schema object
        """
        classification_url = f"{config.API_BASE_URL}/objects/classify"
        
        classification_info = self.object_states[object_id].get('classification_info', {})
        
        classification_payload = {
            "id": object_id,
            "name":payload["name"],
            "type": "arrow",
            "steps":schema_obj["steps"],
            "detailedMessage":payload["detailedMessage"],
            "size": 35,
            "rotation":schema_obj["rotation"],
            "speed":schema_obj["speed"],
            "position":schema_obj["position"],
            "details":{
                "origin_country": payload.get("originCountry"),
                "direction":"175",
                "moving_to":payload.get("moving_to")
            },
            "plots": schema_obj.get("plots", []),
            "description": classification_info.get("suggestion_reason", ""),
            "classification": {
                "current_identification": None,
                "suggested_identification": classification_info.get("suggested_identification", "drone"),
                "suggestion_reason": classification_info.get("suggestion_reason", "")
            },
            "qna": [
                {
                    "question": "מתי ואיך אני נדרש לפעול על הכטבם",
                    "answers": [
                        'יש לפעול מיידית על המטרה כאשר ההחלטה לסווג זוהה ככטב"ם אויב',
                        "כרוז צוות ליירוט",
                        "זנק מסוקי קרב",
                        "זנק מטוסי קרב",
                        "העלה כוננות לסוללות הטילים",
                        "העלה מעגל שליטה",
                        "העלה חוסמי gps"
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
            ]
        }
        
        try:
            response = requests.post(classification_url, json=classification_payload)
            response.raise_for_status()
            if payload.get("name") == "ב149":
                time.sleep(10)
            print(f"  [CLASSIFY] Sent classification suggestion for {object_id}")
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to send classification for {object_id}: {e}")

    @staticmethod
    def transform_to_schema(firebase_obj):
        """
        Transform Firebase object to the target API schema.

        Args:
            firebase_obj: The Firebase document object with children

        Returns:
            dict: Transformed object matching the target schema
        """
        # Extract basic information
        obj_id = firebase_obj.get('_id', '')

        # Get starting position (lat, lon, altitude)
        starting_point = firebase_obj.get('ending_point', {})
        starting_lat = starting_point.get('lat', 0)
        starting_lon = starting_point.get('lon', 0)
        starting_altitude = firebase_obj.get('points', [{}])[0].get('altitude', 0) if firebase_obj.get('points') else 0

        # Transform points to plots
        plots = []
        points = firebase_obj.get('points', [])

        prev_point = None
        for i, point in enumerate(points):
            # Use rotation from point data if available, otherwise calculate it
            rotation = point.get('rotation')
            if rotation is None:
                rotation = 0
                if prev_point is not None:
                    prev_lat = prev_point.get('lat', 0)
                    prev_lon = prev_point.get('lon', 0)
                    curr_lat = point.get('lat', 0)
                    curr_lon = point.get('lon', 0)

                    # Only calculate if points are different
                    if (prev_lat != curr_lat or prev_lon != curr_lon):
                        rotation = calculate_bearing(prev_lat, prev_lon, curr_lat, curr_lon) - 90

            plot = {
                "position": [
                    point.get('lon', 0),
                    point.get('lat', 0),
                    point.get('altitude', 0)
                ],
                "time": point.get('timestamp').isoformat() if point.get('timestamp') and not isinstance(point.get('timestamp'), str) else "",
                "color": firebase_obj.get("color_on_map"),
                "rotation": rotation
            }
            plots.append(plot)
            prev_point = point

        # Remove last point from plots
        plots = plots[:-1]

        # Get rotation for the current position (last point)
        last_rotation = 0
        if len(points) >= 1:
            # Use rotation from last point if available
            last_rotation = points[-1].get('rotation')
            if last_rotation is None:
                # Fallback to calculation if not available
                last_rotation = 0
                if len(points) >= 2:
                    prev_lat = points[-2].get('lat', 0)
                    prev_lon = points[-2].get('lon', 0)
                    curr_lat = points[-1].get('lat', 0)
                    curr_lon = points[-1].get('lon', 0)

                    if (prev_lat != curr_lat or prev_lon != curr_lon):
                        last_rotation = calculate_bearing(prev_lat, prev_lon, curr_lat, curr_lon) - 90

        # Prepare classification based on object type
        classification = None
        steps = None
        if firebase_obj.get("should_classify"):
            # Object has classification info - include it in EVERY update
            classification_info = firebase_obj.get("classification_info", {})
            steps = firebase_obj.get("steps")
            classification = {
                "current_identification": None,
                "suggested_identification": classification_info.get("suggested_identification", "drone"),
                "suggestion_reason": classification_info.get("suggestion_reason", "")
            }
        elif firebase_obj.get("object_type") and firebase_obj.get("object_type") != "unknownFast":
            # Regular object with known type
            classification = {"current_identification": firebase_obj.get("object_type")}
        
        # Create the final schema object
        schema_obj = {
            "id": obj_id,
            "speed": firebase_obj.get('avg_speed', 0),
            "type": firebase_obj.get("object_type"),
            "position": [
                points[-1].get('lon', 0) if points else starting_lon,
                points[-1].get('lat', 0) if points else starting_lat,
                points[-1].get('altitude', 0) if points else starting_altitude
            ],
            "color": firebase_obj.get("color_on_map"),
            "size": 100 if firebase_obj.get("object_type") not in ['bird', 'arrow'] else 30,
            "rotation": last_rotation,
            "plots": plots,
            "classification": classification,
            "steps":steps
        }
        
        # Add name if available
        if firebase_obj.get("name"):
            schema_obj["name"] = firebase_obj.get("name")
        
        # Add details
        details = firebase_obj.copy()
        if details.get("points"):
            details.pop("points")
        if details.get("total_distance_simulated"):
            details.pop("total_distance_simulated")
        if details.get("total_distance"):
            details.pop("total_distance")

        details = ObjectSimulator.convert_datetimes_to_iso(details)
        if firebase_obj.get("object_type"):
            details["type"] = firebase_obj["object_type"]
        schema_obj["details"] = details
        
        return schema_obj
    @staticmethod
    def convert_datetimes_to_iso(obj):
        """Recursively convert all datetime/date objects in a dict or list to ISO format strings."""
        if isinstance(obj, dict):
            return {k: ObjectSimulator.convert_datetimes_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ObjectSimulator.convert_datetimes_to_iso(i) for i in obj]
        elif isinstance(obj, (datetime)):
            return obj.isoformat()
        else:
            return obj
    def _check_inactive_objects(self) -> Set[str]:
        """
        Check for objects that haven't been updated recently
        
        Returns:
            Set of object IDs that should be marked as deleted
        """
        inactive_objects = set()

        for object_id in self.object_states.keys():
            last_update = self.last_update_time.get(object_id, 0)
            time_since_update = self.current_simulation_time - last_update

            # Only check objects that have been updated at least once
            if object_id in self.last_update_time and time_since_update >= config.INACTIVITY_TIMEOUT:
                inactive_objects.add(object_id)

        return inactive_objects

    def run(self):
        """
        Main simulation loop
        
        Note: Drone attacks are now triggered manually via trigger_drone_attack.py
        """
        if not self.prepare_simulation():
            return

        print("\n" + "=" * 60)
        print("Starting simulation...")
        print("=" * 60 + "\n")

        real_start_time = time.time()
        total_duration = self._get_total_duration()
        objects_marked_deleted = set()

        while self.current_simulation_time <= total_duration:
            tick_start = time.time()

            # Get points that should be processed at this time
            points_to_process = self._get_points_to_process()

            if points_to_process:
                print(f"[T+{self.current_simulation_time:.1f}s] Processing {len(points_to_process)} points...")

                # Group points by object ID
                updates_by_object = {}
                for item in points_to_process:
                    obj_id = item['object_id']
                    if obj_id not in updates_by_object:
                        updates_by_object[obj_id] = []
                    updates_by_object[obj_id].append(item)

                # Update each object and send to API
                for object_id, items in updates_by_object.items():
                    for item in items:
                        self._update_object_state(object_id, item['point'])
                        self.processed_point_indices.add(item['index'])

                    # Send update after all points for this tick are added
                    self._send_object_update(object_id)

            # Check for inactive objects
            inactive_objects = self._check_inactive_objects()
            for object_id in inactive_objects:
                if object_id not in objects_marked_deleted:
                    print(f"[T+{self.current_simulation_time:.1f}s] Marking inactive object as deleted...")
                    self._send_object_update(object_id, is_delete=True)
                    objects_marked_deleted.add(object_id)

            # Move to next time step
            self.current_simulation_time += config.TICK_INTERVAL

            # Sleep to maintain real-time simulation
            elapsed = time.time() - tick_start
            sleep_time = max(0, config.TICK_INTERVAL - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Final summary
        print("\n" + "=" * 60)
        print("Simulation complete!")
        print("=" * 60)
        print(f"Total simulation time: {total_duration:.1f} seconds")
        print(f"Total real time: {time.time() - real_start_time:.1f} seconds")
        print(f"Total points processed: {len(self.processed_point_indices)}")
        print(f"Objects marked as deleted: {len(objects_marked_deleted)}")
