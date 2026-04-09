import re


class FormatterService:

    def __init__(self):
        print("✅ FormatterService initialized")

    # -------------------------------
    # CLEAN VALUE
    # -------------------------------
    def clean(self, text):
        if not text:
            return None

        text = str(text).strip()

        if text.lower() in ["", "not specified", "unknown", "..."]:
            return None

        return text

    # -------------------------------
    # BUILD COMPONENT STRINGS
    # -------------------------------
    def build_components(self, entries):

        components = set()

        for item in entries:

            if not isinstance(item, dict):
                continue

            # Battery
            battery = self.clean(item.get("battery"))
            if battery:
                components.add(f"Battery ({battery})")

            # Camera
            camera = self.clean(item.get("camera"))
            if camera:
                components.add(f"Camera Module ({camera})")

            # Display
            display = self.clean(item.get("display"))
            if display:
                components.add(f"Display Panel ({display})")

            # Processor
            processor = self.clean(item.get("processor"))
            if processor:
                components.add(f"Logic Board ({processor})")

        return list(components)

    # -------------------------------
    # BUILD CAPABILITIES
    # -------------------------------
    def build_capabilities(self, entries):

        capabilities = set()

        for item in entries:

            if not isinstance(item, dict):
                continue

            # Connectivity
            conn = self.clean(item.get("connectivity"))
            if conn:
                capabilities.add("Connectivity Features")

            # Sensors
            sensors = self.clean(item.get("sensors"))
            if sensors:
                capabilities.add("Sensor System")

            # Display → touchscreen
            if self.clean(item.get("display")):
                capabilities.add("Touchscreen")

            # Camera
            if self.clean(item.get("camera")):
                capabilities.add("Camera")

        return list(capabilities)

    # -------------------------------
    # MAIN FORMATTER
    # -------------------------------
    def format(self, structured_data):

        entries = (
            structured_data.get("components", []) +
            structured_data.get("capabilities", [])
        )

        components = self.build_components(entries)
        capabilities = self.build_capabilities(entries)

        return components, capabilities