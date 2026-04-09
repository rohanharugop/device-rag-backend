from typing import Dict, Any

class SessionManager:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def create(self, device_id: str, data: Dict[str, Any]):
        self._store[device_id] = data

    def get(self, device_id: str):
        return self._store.get(device_id)

    def update(self, device_id: str, data: Dict[str, Any]):
        if device_id not in self._store:
            raise ValueError("Invalid device_id")
        self._store[device_id].update(data)

    def exists(self, device_id: str):
        return device_id in self._store


# singleton instance
session_manager = SessionManager()