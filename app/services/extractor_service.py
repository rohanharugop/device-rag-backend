# import re
# import json
# import os
# from openai import OpenAI


# class ExtractorService:

#     def __init__(self):
#         self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         print("✅ ExtractorService (Optimized + Fixed) initialized")

#     # -------------------------------
#     # CLEAN TEXT
#     # -------------------------------
#     def clean_text(self, text):
#         text = re.sub(r'Add comment.*?Cancel Post comment', '', text, flags=re.IGNORECASE)
#         text = re.sub(r'Step \d+', '', text)
#         text = re.sub(r'\s+', ' ', text)
#         return text.strip()

#     # -------------------------------
#     # CHUNKING
#     # -------------------------------
#     def chunk_text(self, text, chunk_size=120, overlap=30):
#         words = text.split()
#         chunks = []
#         i = 0

#         while i < len(words):
#             chunk = words[i:i + chunk_size]
#             chunks.append(" ".join(chunk))
#             i += chunk_size - overlap

#         return chunks

#     # -------------------------------
#     # FILTERS
#     # -------------------------------
#     def is_technical_chunk(self, chunk):
#         keywords = [
#             "mah", "mp", "gb", "hz", "nm",
#             "processor", "chip", "camera",
#             "battery", "display", "sensor",
#             "ram", "storage", "wifi", "bluetooth"
#         ]
#         return any(k in chunk.lower() for k in keywords)

#     def is_junk(self, chunk):
#         junk_patterns = [
#             "login", "sign up", "subscribe",
#             "trending", "advertisement"
#         ]
#         return any(j in chunk.lower() for j in junk_patterns)

#     # -------------------------------
#     # SAFE JSON PARSER
#     # -------------------------------
#     def safe_parse_json(self, text):
#         text = re.sub(r"```json|```", "", text).strip()

#         try:
#             return json.loads(text)
#         except:
#             print("❌ JSON parse failed")
#             return None

#     # -------------------------------
#     # FIXED BATCH SCORING
#     # -------------------------------
#     def score_chunks_batch(self, chunks):

#         prompt = f"""
# Return ONLY a JSON array of numbers (0–10).
# NO explanation.

# Example:
# [5,7,3]

# Chunks:
# {chunks}
# """

#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )

#         content = response.choices[0].message.content.strip()

#         print("🧠 Raw batch response:", content)

#         import re
#         nums = re.findall(r'\d+', content)

#         if not nums:
#             print("❌ Batch parsing failed → fallback")
#             return [5] * len(chunks)  # SAFE fallback

#         return [int(n) for n in nums[:len(chunks)]]

#     # -------------------------------
#     # EXTRACTION
#     # -------------------------------
#     def extract_structured(self, chunk):

#         prompt = f"""
# Extract ONLY real hardware specifications.

# STRICT:
# - Return ONLY JSON
# - No markdown
# - Ignore UI text

# FIELDS:
# battery, camera, display, processor, memory, storage, connectivity, sensors

# TEXT:
# {chunk}
# """

#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )

#         return self.safe_parse_json(response.choices[0].message.content)

#     # -------------------------------
#     # MAIN PIPELINE (FIXED)
#     # -------------------------------
#     def run(self, raw_data):

#         print("\n🚀 EXTRACTOR PIPELINE (FIXED)\n")

#         all_chunks = []

#         # Step 1: Clean + chunk
#         for item in raw_data:
#             text = self.clean_text(item.get("content", ""))

#             if len(text) < 200:
#                 continue

#             all_chunks.extend(self.chunk_text(text))

#         print(f"📦 TOTAL RAW CHUNKS: {len(all_chunks)}")

#         # Step 2: Filter
#         filtered_chunks = [
#             c for c in all_chunks
#             if not self.is_junk(c) and self.is_technical_chunk(c)
#         ]

#         print(f"📉 After filtering: {len(filtered_chunks)}")

#         # Step 3: Batch scoring
#         final_chunks = []

#         if filtered_chunks:
#             scores = self.score_chunks_batch(filtered_chunks)

#             for chunk, score in zip(filtered_chunks, scores):
#                 if score >= 5:
#                     final_chunks.append(chunk)

#         # 🚨 FIX: fallback if empty
#         if not final_chunks:
#             print("⚠️ No chunks passed → fallback")
#             final_chunks = filtered_chunks[:5]

#         print(f"✅ Final chunks: {len(final_chunks)}")

#         # Step 4: Extraction
#         extracted_data = []

#         for chunk in final_chunks:
#             result = self.extract_structured(chunk)

#             if result and any(result.values()):
#                 extracted_data.append(result)

#         print(f"✅ Structured outputs: {len(extracted_data)}")

#         # 🚨 CRITICAL FIX: ALWAYS RETURN DICT
#         if not extracted_data:
#             return {
#                 "components": [],
#                 "capabilities": []
#             }

#         mid = len(extracted_data) // 2

#         return {
#             "components": extracted_data[:mid],
#             "capabilities": extracted_data[mid:]
#         }


import re
import json
import os
from openai import OpenAI


class ExtractorService:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ ExtractorService (STABLE VERSION) initialized")

    # -------------------------------
    # CLEAN TEXT
    # -------------------------------
    def clean_text(self, text):
        text = re.sub(r'Add comment.*?Cancel Post comment', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Step \d+', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # -------------------------------
    # CHUNKING (LARGER CHUNKS)
    # -------------------------------
    def chunk_text(self, text, chunk_size=200, overlap=50):
        words = text.split()
        chunks = []
        i = 0

        while i < len(words):
            chunk = words[i:i + chunk_size]
            chunks.append(" ".join(chunk))
            i += chunk_size - overlap

        return chunks

    # -------------------------------
    # LIGHT FILTER (RELAXED)
    # -------------------------------
    def is_junk(self, chunk):
        junk_patterns = ["login", "sign up", "subscribe"]
        return any(j in chunk.lower() for j in junk_patterns)

    # -------------------------------
    # SAFE JSON PARSER
    # -------------------------------
    def safe_parse_json(self, text):
        text = re.sub(r"```json|```", "", text).strip()

        try:
            return json.loads(text)
        except:
            return None

    # -------------------------------
    # EXTRACTION (STRONG PROMPT)
    # -------------------------------
    def extract_structured(self, chunk):

        prompt = f"""
Extract ONLY REAL hardware specifications from the text.

STRICT RULES:
- DO NOT return "Not specified"
- DO NOT hallucinate
- Only extract if explicitly present
- Ignore UI text, navigation, ads

RETURN JSON ONLY:

{{
  "battery": "...",
  "camera": "...",
  "display": "...",
  "processor": "...",
  "memory": "...",
  "storage": "...",
  "connectivity": "...",
  "sensors": "..."
}}

TEXT:
{chunk}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return self.safe_parse_json(response.choices[0].message.content)

    # -------------------------------
    # MAIN PIPELINE (FIXED)
    # -------------------------------
    def run(self, raw_data):

        print("\n🚀 EXTRACTOR PIPELINE (OPTIMIZED)\n")

        all_chunks = []

        # Step 1: Clean + chunk
        for item in raw_data:
            text = self.clean_text(item.get("content", ""))

            if len(text) < 300:
                continue

            all_chunks.extend(self.chunk_text(text))

        print(f"📦 TOTAL RAW CHUNKS: {len(all_chunks)}")

        # Step 2: LIGHT FILTER ONLY
        filtered_chunks = [
            c for c in all_chunks if not self.is_junk(c)
        ]

        print(f"📉 After filtering: {len(filtered_chunks)}")

        # 🚨 NO SCORING — KEEP MORE DATA
        final_chunks = filtered_chunks[:15]  # limit cost

        print(f"✅ Final chunks: {len(final_chunks)}")

        # Step 3: Extraction
        extracted_data = []

        for chunk in final_chunks:
            result = self.extract_structured(chunk)

            if result and any(
                v and str(v).lower() not in ["not specified", "unknown"]
                for v in result.values()
            ):
                extracted_data.append(result)

        print(f"✅ Structured outputs: {len(extracted_data)}")

        if not extracted_data:
            print("⚠️ Extraction failed → returning fallback")

            return {
                "components": [{"raw_text": c} for c in final_chunks[:3]],
                "capabilities": []
            }

        mid = len(extracted_data) // 2

        return {
            "components": extracted_data[:mid],
            "capabilities": extracted_data[mid:]
        }