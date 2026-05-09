import json
import os


class RequirementMapperAgent:

    def __init__(self):
        self.template_dir = "app/templates"

    def load_requirements(self, template_name):
        path = os.path.join(self.template_dir, template_name, "requirements.json")

        if not os.path.exists(path):
            # 🔥 Fail-safe: prevent crash if file missing
            return {
                "hardware": [],
                "software": []
            }

        with open(path) as f:
            return json.load(f)

    def normalize(self, items):
        normalized = set()

        for item in items:
            item = str(item).lower()

            # 🔥 DISPLAY
            if any(x in item for x in ["display", "screen", "oled", "lcd", "retina"]):
                normalized.add("display")

            # 🔥 CAMERA
            if "camera" in item:
                normalized.add("camera")

            # 🔥 STORAGE
            if any(x in item for x in ["storage", "memory", "ssd", "flash"]):
                normalized.add("storage")

            # 🔥 BATTERY
            if "battery" in item:
                normalized.add("battery")

            # 🔥 WIFI
            if "wifi" in item or "wi-fi" in item:
                normalized.add("wifi")

        return normalized

    def check_compatibility(self, device_hw, device_sw, requirements):

        # 🔥 Normalize hardware ONLY
        device_hw = self.normalize(device_hw)

        # 🔥 DO NOT normalize software (keep exact match)
        device_sw = set([str(i).lower().strip() for i in device_sw])

        required_hw = requirements.get("hardware", [])
        required_sw = requirements.get("software", [])

        missing_hw = [req for req in required_hw if req.lower() not in device_hw]
        missing_sw = [req for req in required_sw if req.lower() not in device_sw]

        if missing_hw or missing_sw:
            return False, {
                "missing_hardware": missing_hw,
                "missing_software": missing_sw
            }

        return True, {}

    def evaluate_all(self, templates, device_hw, device_sw):
        results = []

        for template in templates:
            req = self.load_requirements(template)

            ok, issues = self.check_compatibility(device_hw, device_sw, req)

            results.append({
                "template": template,
                "compatible": ok,
                "issues": issues
            })

        return results