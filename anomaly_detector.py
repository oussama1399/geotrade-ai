import json
import os
from welford_utils import Welford

def detect_anomalies_dynamic(json_path: str, field_name: str, base_threshold: float = 3.0, min_points: int = 5):
    """
    Detects anomalies in a JSON file using a one-pass dynamic approach with Welford's algorithm.
    Anomalies are detected based on the statistics of values seen *before* the current point.
    """
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    w = Welford()
    anomalies = []
    processed_count = 0

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            print("Error: JSON data must be a list of objects.")
            return

        print(f"Starting dynamic detection on field '{field_name}'...")

        for item in data:
            val = item.get(field_name)
            if not isinstance(val, (int, float)):
                continue
            
            val = float(val)
            processed_count += 1
            
            # Use current stats to check for anomaly BEFORE updating stats
            # We need a minimum number of points for stable statistics
            if w.k >= min_points:
                z = w.z_score(val)
                # Dynamic adjustment: if variance is very low, we might be too sensitive
                # Or we can strictly use the Z-score threshold
                if abs(z) > base_threshold:
                    item['anomaly_detected'] = True
                    item['z_score'] = z
                    item['stats_at_time'] = {"mean": w.mean, "std_dev": w.std_dev}
                    anomalies.append(item)
                    print(f"!! ANOMALY: Value {val}, Z-Score {z:.2f} (Mean: {w.mean:.2f}, SD: {w.std_dev:.2f})")

            # Update stats with the new point
            w.update(val)

        print(f"Processed {processed_count} points. Stats - Final Mean: {w.mean:.4f}, Final StdDev: {w.std_dev:.4f}")

        if anomalies:
            with open("anomalies_detected.json", "w") as f:
                json.dump(anomalies, f, indent=4)
                print(f"Saved {len(anomalies)} anomalies to anomalies_detected.json")
        else:
            print("No anomalies detected.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example usage:
    dummy_file = "sample_data.json"
    if not os.path.exists(dummy_file):
        # Generate a sequence with a clear outlier
        sample_data = [
            {"value": 10}, {"value": 10.5}, {"value": 9.8}, {"value": 10.2},
            {"value": 10.1}, {"value": 10.0}, {"value": 50.0}, # Sudden anomaly
            {"value": 10.3}, {"value": 9.9}
        ]
        with open(dummy_file, "w") as f:
            json.dump(sample_data, f)
        print(f"Created {dummy_file} for testing.")

    detect_anomalies_dynamic(dummy_file, "value")
