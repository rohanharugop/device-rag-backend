import os
import json
from datetime import datetime


class StorageService:

    def __init__(self):
        self.raw_dir = "data/raw"
        self.processed_dir = "data/processed"

        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    # -------------------------------
    # RAW STORAGE
    # -------------------------------
    def save_raw(self, device_id, data):

        path = os.path.join(self.raw_dir, f"{device_id}.json")

        payload = {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return path

    def load_raw(self, device_id):

        path = os.path.join(self.raw_dir, f"{device_id}.json")

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------
    # PROCESSED STORAGE
    # -------------------------------
    def save_processed(self, device_id, data):

        path = os.path.join(self.processed_dir, f"{device_id}.json")

        payload = {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return path

    def load_processed(self, device_id):

        path = os.path.join(self.processed_dir, f"{device_id}.json")

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)