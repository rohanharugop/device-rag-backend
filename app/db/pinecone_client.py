import os
from pinecone import Pinecone


class PineconeClient:

    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")

        if not api_key:
            raise ValueError("PINECONE_API_KEY not set")

        self.pc = Pinecone(api_key=api_key)

        # ✅ MATCH YOUR EXISTING INDEX
        self.index_name = "device-rag"

        # ✅ DO NOT CREATE NEW INDEX
        self.index = self.pc.Index(self.index_name)

    def upsert(self, vectors):
        self.index.upsert(vectors=vectors)

    def query(self, vector, top_k=5):
        return self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )


pinecone_client = PineconeClient()