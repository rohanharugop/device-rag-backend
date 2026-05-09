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
# CONTROLLED VOCAB (PWA tags)
# -------------------------------
PWA_TAGS = {
    "camera": ["camera", "lens", "photo"],
    "display": ["display", "screen", "oled", "lcd", "retina", "touch"],
    "storage": ["storage", "memory", "ssd", "flash"],
    "battery": ["battery", "mah", "power"],
    "wifi": ["wifi", "wi-fi", "wireless"],
    "bluetooth": ["bluetooth"]
}

def derive_pwa_tags(raw_items):
    """
    Non-destructive: derive coarse tags from raw strings.
    """
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
    # Skip default namespace
    return [ns for ns in namespaces if ns != "__default__"]

def fetch_one(namespace):
    """
    Assumes 1 vector per namespace (as in your current design).
    """
    res = index.query(
        vector=[0.0] * 1536,
        top_k=1,
        namespace=namespace,
        include_metadata=True
    )
    if not res.matches:
        return None
    return res.matches[0]

def safe_json_load(value, default):
    try:
        return json.loads(value) if value is not None else default
    except Exception:
        return default

# -------------------------------
# MAIN
# -------------------------------
def run():
    namespaces = get_namespaces()
    print(f"\n🔍 Found {len(namespaces)} namespaces (excluding __default__)\n")

    for ns in namespaces:
        print("\n=================================================")
        print(f"📦 Namespace: {ns}")
        print("=================================================")

        match = fetch_one(ns)
        if not match:
            print("⚠️ No data found → skipping")
            continue

        md = match.metadata or {}

        # Skip if already augmented (idempotent)
        if "pwa_capability_tags" in md:
            print("⚡ Already has pwa_capability_tags → skipping")
            continue

        # -------------------------------
        # READ EXISTING DATA (DO NOT MODIFY)
        # -------------------------------
        components = safe_json_load(md.get("components"), [])
        # support both old and new keys safely
        capabilities = safe_json_load(md.get("capabilities"), [])
        capabilities_raw = safe_json_load(md.get("capabilities_raw"), capabilities)

        # Combine for tag derivation only (non-destructive)
        combined = []
        if isinstance(components, list):
            combined.extend(components)
        if isinstance(capabilities_raw, list):
            combined.extend(capabilities_raw)

        # -------------------------------
        # DERIVE NEW TAGS (FOR PWA ONLY)
        # -------------------------------
        pwa_tags = derive_pwa_tags(combined)

        # -------------------------------
        # PREVIEW (NO MUTATION YET)
        # -------------------------------
        print("\n📥 ORIGINAL (unchanged)")
        print(f"- components (sample): {components[:3]}")
        print(f"- capabilities (sample): {capabilities[:3]}")
        if capabilities_raw != capabilities:
            print(f"- capabilities_raw (sample): {capabilities_raw[:3]}")

        print("\n🧠 NEW FIELD (will be ADDED, not replacing anything)")
        print(f"- pwa_capability_tags: {pwa_tags}")

        # -------------------------------
        # CONFIRMATION
        # -------------------------------
        choice = input("\n👉 Apply augmentation? (y / n / skip all): ").strip().lower()

        if choice == "skip all":
            print("🚫 Aborted by user")
            break

        if choice != "y":
            print("⏭️ Skipped")
            continue

        # -------------------------------
        # BUILD NEW METADATA (NON-DESTRUCTIVE)
        # -------------------------------
        # Preserve everything as-is, only ADD new field
        new_md = dict(md)  # shallow copy is fine (values are strings)

        new_md["pwa_capability_tags"] = json.dumps(pwa_tags)
        # Optional marker so you can track augmentation separately from other versions
        new_md["pwa_tags_version"] = "v1"

        # -------------------------------
        # UPSERT (SAME ID, SAME VECTOR, NEW METADATA)
        # -------------------------------
        try:
            index.upsert(
                vectors=[{
                    "id": match.id,
                    "values": match.values,   # preserve original embedding
                    "metadata": new_md        # only addition
                }],
                namespace=ns
            )
            print("✅ Augmented successfully (no fields overwritten)")
        except Exception as e:
            print("❌ Failed to update:", str(e))

    print("\n🎉 Augmentation complete (non-destructive).")

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    run()