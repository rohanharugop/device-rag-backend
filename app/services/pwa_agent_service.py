class PWAAgentService:

    def decide(self, capabilities):
        capabilities = [c.lower() for c in capabilities]

        if "camera" in " ".join(capabilities):
            return "security_cam"

        if "wifi" in " ".join(capabilities) and "display" in " ".join(capabilities):
            return "dashboard"

        if "storage" in " ".join(capabilities):
            return "media_server"

        return "dashboard"  # fallback