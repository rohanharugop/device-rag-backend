import os
from pinecone import Pinecone


class PineconeClient:

    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")

        if not api_key:
            raise Exception("❌ PINECONE_API_KEY not set")

        try:
            self.pc = Pinecone(api_key=api_key)
            self.index_name = "device-rag"
            self.index = self.pc.Index(self.index_name)

            print("✅ Pinecone client initialized")

        except Exception as e:
            raise Exception(f"❌ Pinecone init failed: {str(e)}")

    def upsert(self, vectors, namespace):
        self.index.upsert(
            vectors=vectors,
            namespace=namespace
        )

    def query(self, vector, namespace, top_k=1):
        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True
        )


# ✅ LAZY FACTORY (CRITICAL FIX)
def get_pinecone_client():
    return PineconeClient()