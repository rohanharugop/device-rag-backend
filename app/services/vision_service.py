# import torch
# from PIL import Image
# from transformers import BlipProcessor, BlipForConditionalGeneration
# import io
# import re


# class VisionService:
#     _model = None
#     _processor = None
#     _device = "cuda" if torch.cuda.is_available() else "cpu"

#     def __init__(self):
#         # Lazy load model
#         if VisionService._model is None:
#             print("🧠 Loading BLIP model...")

#             VisionService._processor = BlipProcessor.from_pretrained(
#                 "Salesforce/blip-image-captioning-base"
#             )
#             VisionService._model = BlipForConditionalGeneration.from_pretrained(
#                 "Salesforce/blip-image-captioning-base"
#             )

#             VisionService._model.to(self._device)

#             print(f"✅ Vision model loaded on {self._device}")

#     # -------------------------------
#     # STEP 1: Generate Caption
#     # -------------------------------
#     def generate_caption(self, image_bytes):
#         try:
#             image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#         except Exception as e:
#             raise Exception(f"Image processing failed: {str(e)}")

#         inputs = VisionService._processor(image, return_tensors="pt").to(self._device)

#         out = VisionService._model.generate(**inputs, max_new_tokens=50)
#         caption = VisionService._processor.decode(out[0], skip_special_tokens=True)

#         print("🧠 Caption:", caption)

#         return caption.lower()

#     # -------------------------------
#     # STEP 2: Extract Model
#     # -------------------------------
#     def extract_model(self, caption):
#         patterns = [
#             r"iphone\s*(\d+)",
#             r"samsung\s*(s\d+)",
#             r"pixel\s*(\d+)"
#         ]

#         for p in patterns:
#             match = re.search(p, caption)
#             if match:
#                 return match.group(1)

#         return None

#     # -------------------------------
#     # STEP 3: Extract Device Info
#     # -------------------------------
#     def extract_device_info(self, caption):

#         brand_map = {
#             "iphone": "Apple",
#             "macbook": "Apple"
#         }

#         brands = [
#             "iphone", "apple", "samsung", "dell", "hp",
#             "lenovo", "oneplus", "xiaomi", "realme",
#             "oppo", "vivo", "asus", "acer", "macbook"
#         ]

#         detected_brand = None

#         for brand in brands:
#             if brand in caption:
#                 detected_brand = brand_map.get(brand, brand.capitalize())
#                 break

#         # Detect device type
#         if "phone" in caption or "smartphone" in caption:
#             device_type = "smartphone"
#         elif "laptop" in caption:
#             device_type = "laptop"
#         elif "tablet" in caption:
#             device_type = "tablet"
#         else:
#             device_type = "device"

#         model = self.extract_model(caption)

#         return {
#             "brand": detected_brand if detected_brand else "Unknown",
#             "model": model if model else device_type,
#             "confidence": 0.75
#         }

#     # -------------------------------
#     # MAIN ENTRY
#     # -------------------------------
#     def detect(self, image_bytes):
#         caption = self.generate_caption(image_bytes)
#         result = self.extract_device_info(caption)
#         return result
















import os
import base64
from openai import OpenAI
import re


class VisionService:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def detect(self, image_bytes):

        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """
You are an expert in identifying electronic devices.

Analyze the image and return:

- Brand (Apple, Samsung, etc.)
- Exact Model (e.g., iPhone 12, Samsung Galaxy S21)

Rules:
- Be as specific as possible
- DO NOT return generic names like "smartphone"

Output format:

Brand: <brand>
Model: <model>
Confidence: <0-1>
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ],
                }
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content.strip()

        print("\n🧠 OPENAI VISION RAW OUTPUT:\n", text)

        return self._parse_response(text)

    def _parse_response(self, text):

        brand_match = re.search(r"Brand:\s*(.*)", text)
        model_match = re.search(r"Model:\s*(.*)", text)
        confidence_match = re.search(r"Confidence:\s*(.*)", text)

        brand = brand_match.group(1).strip() if brand_match else "Unknown"
        model = model_match.group(1).strip() if model_match else "device"

        try:
            confidence = float(confidence_match.group(1).strip())
        except:
            confidence = 0.85

        return {
            "brand": brand,
            "model": model,
            "confidence": confidence
        }