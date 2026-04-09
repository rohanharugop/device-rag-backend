# import os
# import re
# import json
# from openai import OpenAI
# from app.db.pinecone_client import pinecone_client


# class RAGService:

#     def __init__(self):
#         self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         print("✅ RAG Service initialized")

#     # -------------------------------
#     # NORMALIZE DEVICE NAME
#     # -------------------------------
#     def get_namespace(self, device_name):
#         namespace = re.sub(r'[^a-z0-9]+', '_', device_name.lower()).strip("_")
#         print(f"🧭 Namespace: {namespace}")
#         return namespace

#     # -------------------------------
#     # CACHE CHECK
#     # -------------------------------
#     def exists(self, device_name):
#         namespace = self.get_namespace(device_name)

#         stats = pinecone_client.index.describe_index_stats()
#         namespaces = stats.get("namespaces", {})

#         exists = namespace in namespaces and namespaces[namespace]["vector_count"] > 0

#         print(f"📦 Namespace exists: {exists}")
#         return exists

#     # -------------------------------
#     # EMBEDDING
#     # -------------------------------
#     def embed(self, text):
#         response = self.client.embeddings.create(
#             model="text-embedding-3-small",
#             input=[text]
#         )
#         return response.data[0].embedding

#     # -------------------------------
#     # STORE (FIXED + SAFE)
#     # -------------------------------
#     def store(self, device_name, processed_data):

#         namespace = self.get_namespace(device_name)

#         print("\n📦 STORAGE STEP\n")

#         try:
#             # -------------------------------
#             # FLATTEN METADATA
#             # -------------------------------
#             flat_metadata = {}

#             def flatten(prefix, obj):
#                 if isinstance(obj, dict):
#                     for k, v in obj.items():
#                         flatten(f"{prefix}_{k}", v)
#                 elif isinstance(obj, list):
#                     flat_metadata[prefix] = ", ".join(
#                         str(item) if not isinstance(item, dict)
#                         else json.dumps(item)
#                         for item in obj
#                     )
#                 else:
#                     flat_metadata[prefix] = str(obj)

#             flatten("data", processed_data)

#             print("📦 METADATA PREVIEW:")
#             for k, v in list(flat_metadata.items())[:5]:
#                 print(k, ":", v[:80])

#             # -------------------------------
#             # EMBEDDING
#             # -------------------------------
#             text_data = json.dumps(processed_data)
#             embedding = self.embed(text_data)

#             # -------------------------------
#             # UPSERT
#             # -------------------------------
#             pinecone_client.index.upsert(
#                 vectors=[{
#                     "id": namespace,
#                     "values": embedding,
#                     "metadata": flat_metadata
#                 }],
#                 namespace=namespace
#             )

#             print("✅ Stored successfully")

#         except Exception as e:
#             print("❌ Pinecone store failed:", str(e))

#     # -------------------------------
#     # QUERY
#     # -------------------------------
#     def query(self, device_name):

#         namespace = self.get_namespace(device_name)

#         results = pinecone_client.index.query(
#             vector=[0.0] * 1536,
#             top_k=1,
#             namespace=namespace,
#             include_metadata=True
#         )

#         if not results.matches:
#             return {}

#         metadata = results.matches[0].metadata

#         print("🧠 RAW METADATA:", metadata)

#         components = []
#         capabilities = []

#         for k, v in metadata.items():
#             if "components" in k:
#                 components.append(v)
#             elif "capabilities" in k:
#                 capabilities.append(v)

#         return {
#             "components": components,
#             "capabilities": capabilities
#         }


# # -------------------------------
# # SINGLE INSTANCE
# # -------------------------------
# rag_service = RAGService()


















import os
import re
import json
from openai import OpenAI
from app.db.pinecone_client import pinecone_client


class RAGService:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ RAG Service initialized")

    # -------------------------------
    # NORMALIZE DEVICE NAME
    # -------------------------------
    def get_namespace(self, device_name):
        namespace = re.sub(r'[^a-z0-9]+', '_', device_name.lower()).strip("_")
        print(f"🧭 Namespace: {namespace}")
        return namespace

    # -------------------------------
    # CACHE CHECK
    # -------------------------------
    def exists(self, device_name):
        namespace = self.get_namespace(device_name)

        stats = pinecone_client.index.describe_index_stats()
        namespaces = stats.get("namespaces", {})

        exists = namespace in namespaces and namespaces[namespace]["vector_count"] > 0

        print(f"📦 Namespace exists: {exists}")
        return exists

    # -------------------------------
    # EMBEDDING
    # -------------------------------
    def embed(self, text):
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        return response.data[0].embedding

    # -------------------------------
    # STORE (UPDATED FOR FINAL FORMAT)
    # -------------------------------
    def store(self, device_name, formatted_data):

        namespace = self.get_namespace(device_name)

        print("\n📦 STORAGE STEP (FORMATTED DATA)\n")

        try:
            # -------------------------------
            # STORE CLEAN STRUCTURE AS STRING
            # -------------------------------
            metadata = {
                "components": json.dumps(formatted_data.get("components", [])),
                "capabilities": json.dumps(formatted_data.get("capabilities", []))
            }

            print("📦 FINAL STORED DATA PREVIEW:")
            print(metadata)

            # -------------------------------
            # EMBEDDING
            # -------------------------------
            text_data = json.dumps(formatted_data)
            embedding = self.embed(text_data)

            # -------------------------------
            # UPSERT
            # -------------------------------
            pinecone_client.index.upsert(
                vectors=[{
                    "id": namespace,
                    "values": embedding,
                    "metadata": metadata
                }],
                namespace=namespace
            )

            print("✅ Stored successfully")

        except Exception as e:
            print("❌ Pinecone store failed:", str(e))

    # -------------------------------
    # QUERY (UPDATED CLEAN RETURN)
    # -------------------------------
    def query(self, device_name):

        namespace = self.get_namespace(device_name)

        print(f"\n📥 QUERYING: {namespace}")

        results = pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1,
            namespace=namespace,
            include_metadata=True
        )

        if not results.matches:
            print("⚠️ No matches found")
            return {}

        metadata = results.matches[0].metadata

        print("🧠 RAW METADATA:", metadata)

        # -------------------------------
        # ✅ NEW FORMAT (CORRECT)
        # -------------------------------
        if "components" in metadata:
            try:
                return {
                    "components": json.loads(metadata.get("components", "[]")),
                    "capabilities": json.loads(metadata.get("capabilities", "[]"))
                }
            except:
                print("❌ Failed parsing new format")
                return {}

        # -------------------------------
        # ⚠️ OLD FORMAT (FALLBACK SUPPORT)
        # -------------------------------
        print("⚠️ Detected OLD metadata format → attempting recovery")

        components = []
        capabilities = []

        try:
            raw_components = metadata.get("data_components", "")
            raw_capabilities = metadata.get("data_capabilities", "")

            # extract JSON objects
            comp_matches = re.findall(r'\{.*?\}', raw_components)
            cap_matches = re.findall(r'\{.*?\}', raw_capabilities)

            for item in comp_matches:
                parsed = json.loads(item)
                components.append(
                    ", ".join(f"{k}: {v}" for k, v in parsed.items() if v)
                )

            for item in cap_matches:
                parsed = json.loads(item)
                capabilities.append(
                    ", ".join(f"{k}: {v}" for k, v in parsed.items() if v)
                )

        except Exception as e:
            print("❌ Old format recovery failed:", str(e))

        return {
            "components": components[:5],
            "capabilities": capabilities[:5]
        }


# -------------------------------
# SINGLE INSTANCE
# -------------------------------
rag_service = RAGService()