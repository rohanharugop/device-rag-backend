from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Optional: central config access
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")