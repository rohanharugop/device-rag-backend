import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone

# -------------------------------
# LOAD ENV
# -------------------------------
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

if not PINECONE_API_KEY or not PINECONE_INDEX:
    raise ValueError("❌ Missing PINECONE_API_KEY or PINECONE_INDEX")

# -------------------------------
# INIT PINECONE
# -------------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# -------------------------------
# TAG RULES
# -------------------------------
PWA_TAGS = {
    "camera": ["camera", "lens", "photo"],
    "display": ["display", "screen", "oled", "lcd", "retina", "touch"],
    "storage": ["storage", "memory", "ssd", "flash"],
    "battery": ["battery", "mah", "power"],
    "wifi": ["wifi", "wi-fi", "wireless"],
    "bluetooth": ["bluetooth"]
}

def derive_tags(raw_items):
    tags = set()
    for item in raw_items:
        text = str(item).lower()
        for tag, keywords in PWA_TAGS.items():
            if any(k in text for k in keywords):
                tags.add(tag)
    return sorted(list(tags))

# -------------------------------
# HELPERS
# -------------------------------
def get_namespaces():
    stats = index.describe_index_stats()
    namespaces = list(stats.get("namespaces", {}).keys())
    return [ns for ns in namespaces if ns != "__default__"]

def fetch(namespace):
    res = index.query(
    vector=[0.0] * 1536,
    top_k=1,
    namespace=namespace,
    include_metadata=True,
    include_values=True   # 🔥 THIS IS THE FIX
)
    if not res.matches:
        return None
    return res.matches[0]

def safe_load(value):
    try:
        return json.loads(value) if value else []
    except:
        return []

# -------------------------------
# MAIN
# -------------------------------
def migrate():
    namespaces = get_namespaces()

    print(f"\n🔍 Found {len(namespaces)} namespaces (excluding __default__)\n")

    for ns in namespaces:
        print("\n=================================================")
        print(f"📦 Namespace: {ns}")
        print("=================================================")

        match = fetch(ns)
        if not match:
            print("⚠️ No data found → skipping")
            continue

        old_md = match.metadata or {}

        # Skip if already augmented
        if "pwa_capability_tags" in old_md:
            print("⚡ Already has pwa_capability_tags → skipping")
            continue

        # -------------------------------
        # PARSE EXISTING
        # -------------------------------
        combined = []

        # Case 1: structured lists (old pipeline)
        if "components" in old_md:
            combined.extend(safe_load(old_md.get("components")))

        if "capabilities" in old_md:
            combined.extend(safe_load(old_md.get("capabilities")))

        # Case 2: key-value spec format (your current example)
        for key, value in old_md.items():
            if key.startswith("pwa_") or key == "version":
                continue

            # Only extract meaningful string values
            if isinstance(value, str):
                combined.append(f"{key}: {value}")
        tags = derive_tags(combined)

        # -------------------------------
        # BUILD NEW METADATA (NON-DESTRUCTIVE)
        # -------------------------------
        new_md = dict(old_md)
        new_md["pwa_capability_tags"] = json.dumps(tags)
        new_md["pwa_tags_version"] = "v1"

        # -------------------------------
        # PRINT FULL JSON (BEFORE / AFTER)
        # -------------------------------
        print("\n📥 FULL ORIGINAL METADATA:")
        print(json.dumps(old_md, indent=2))

        print("\n🧠 FULL NEW METADATA (TO BE WRITTEN):")
        print(json.dumps(new_md, indent=2))

        # -------------------------------
        # HIGHLIGHT WHAT CHANGED
        # -------------------------------
        print("\n🔍 CHANGE SUMMARY:")
        print("➕ Added: pwa_capability_tags =", tags)
        print("➕ Added: pwa_tags_version = v1")
        print("❌ Removed: NOTHING")
        print("✏️ Modified: NOTHING")

        # -------------------------------
        # CONFIRMATION
        # -------------------------------
        choice = input("\n👉 Apply update? (y / n / skip all): ").strip().lower()

        if choice == "skip all":
            print("🚫 Aborted by user")
            break

        if choice != "y":
            print("⏭️ Skipped")
            continue

        # -------------------------------
        # UPSERT
        # -------------------------------
        try:
            index.upsert(
                vectors=[{
                    "id": match.id,
                    "values": match.values,
                    "metadata": new_md
                }],
                namespace=ns
            )
            print("✅ Successfully updated (no data loss)")
        except Exception as e:
            print("❌ Update failed:", str(e))

    print("\n🎉 Migration complete")


if __name__ == "__main__":
    migrate()