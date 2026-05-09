import os
import shutil
import json

class PWAGeneratorService:

    def generate(self, template_name, device_id, config):
        template_path = f"app/templates/{template_name}"
        output_path = f"generated/{device_id}_{template_name}"

        # Copy template
        if os.path.exists(output_path):
            shutil.rmtree(output_path)

        shutil.copytree(template_path, output_path)

        # Inject config
        config_path = os.path.join(output_path, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Zip it
        zip_path = shutil.make_archive(output_path, 'zip', output_path)

        return zip_path