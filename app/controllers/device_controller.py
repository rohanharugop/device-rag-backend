from uuid import uuid4
from app.core.session_manager import session_manager
from app.services.vision_service import VisionService
from fastapi import HTTPException
from app.core.session_manager import session_manager
from app.services.search_service import SearchService
from app.services.scraper_service import ScraperService
from app.services.extractor_service import ExtractorService
from app.services.rag_service import RAGService
from app.services.generator_service import GeneratorService
from app.services.storage_service import StorageService
from app.services.formatter_service import FormatterService
import traceback







  


def clean_input(value):
    return value if value and value.lower() != "string" else None

class DeviceController:

    @staticmethod
    async def detect_device(file_bytes, brand, model, condition, additional_info):
        vision_service = VisionService()

        result = vision_service.detect(file_bytes)

        device_id = "dev_" + str(uuid4())

        # ✅ Clean user input
        brand = clean_input(brand) or result["brand"]
        model = clean_input(model) or result["model"]

        session_manager.create(device_id, {
            "brand": brand,
            "model": model,
            "condition": condition,
            "notes": additional_info
        })

        return {
            "device_id": device_id,
            "brand": brand,
            "model": model,
            "confidence": result["confidence"]
        }
    
    @staticmethod
    def confirm_device(device_id: str, brand: str, model: str):

        if not session_manager.exists(device_id):
            raise HTTPException(404, "Invalid device_id")

        device_name = f"{brand} {model}"

        session_manager.update(device_id, {
            "brand": brand,
            "model": model,
            "device_name": device_name
        })

        print(f"✅ Device confirmed: {device_name}")

        return {
            "device_id": device_id,
            "device_name": device_name
        }
    @staticmethod
    def device_specs(device_id: str, device_name: str):
        scraper_service = ScraperService()
        extractor_service = ExtractorService()
        formatter = FormatterService()
        rag_service = RAGService()
        print("\n🚀 DEVICE SPECS PIPELINE\n")

        if not session_manager.exists(device_id):
            raise HTTPException(404, "Invalid device_id")

        # -------------------------------
        # CACHE
        # -------------------------------
        if rag_service.exists(device_name):
            print("⚡ CACHE HIT")

            data = rag_service.query(device_name)

            return {
                "device_id": device_id,
                "components": data.get("components", []),
                "capabilities": data.get("capabilities", []),
                "sources": ["cache"]
            }

        print("🚀 CACHE MISS → FULL PIPELINE")

        # -------------------------------
        # SEARCH
        # -------------------------------
        search_service = SearchService()
        urls = search_service.run(device_name)
        print("🔍 URL PREVIEW:", urls[:2])

        # -------------------------------
        # SCRAPE
        # -------------------------------
        raw_data = scraper_service.run(urls)

        if not raw_data:
            print("⚠️ Primary scrape failed → fallback search")
            urls = search_service.fallback_search(device_name)
            raw_data = scraper_service.run(urls)

        if not raw_data:
            print("❌ No data found after fallback")
            return {
                "device_id": device_id,
                "components": [],
                "capabilities": [],
                "sources": []
            }

        print(f"📦 SCRAPED PAGES: {len(raw_data)}")

        # -------------------------------
        # EXTRACT
        # -------------------------------
        structured = extractor_service.run(raw_data)

        print("\n🧠 STRUCTURED OUTPUT PREVIEW:")
        print(structured)

        if not structured or not isinstance(structured, dict):
            print("❌ Extraction failed")
            return {
                "device_id": device_id,
                "components": [],
                "capabilities": [],
                "sources": []
            }

        # -------------------------------
        # FORMAT (🔥 CRITICAL STEP)
        # -------------------------------
        formatter = FormatterService()
        components, capabilities = formatter.format(structured)

        print("\n🧩 FORMATTED OUTPUT:")
        print("Components:", components[:3])
        print("Capabilities:", capabilities[:3])

        # 🚨 SAFETY CHECK (VERY IMPORTANT)
        if not components and not capabilities:
            print("❌ Formatter produced empty output → aborting store")

            return {
                "device_id": device_id,
                "components": [],
                "capabilities": [],
                "sources": []
            }

        formatted_data = {
            "components": components,
            "capabilities": capabilities
        }

        # -------------------------------
        # STORE (✅ FIXED)
        # -------------------------------
        rag_service.store(device_name, formatted_data)

        # -------------------------------
        # FINAL RESPONSE
        # -------------------------------
        return {
            "device_id": device_id,
            "components": components,
            "capabilities": capabilities,
            "sources": [u["link"] for u in urls[:3]]
        }
            
    @staticmethod
    def save_device(device_id: str, components, capabilities):
        rag_service = RAGService()

        # ✅ Validate session
        if not session_manager.exists(device_id):
            raise HTTPException(
                status_code=404,
                detail="Invalid device_id. Session not found."
            )

        try:
            # ✅ Store in session (optional but useful)
            session_manager.update(device_id, {
                "components": components,
                "capabilities": capabilities
            })

            # 🔥 RAG storage
            rag_service.store(device_id, components, capabilities)

            return {"status": "saved"}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"RAG storage failed: {str(e)}"
            )
        
    @staticmethod
    def generate_ideas(device_id: str):
        generator_service = GeneratorService()
        rag_service = RAGService()

        # ✅ Validate session
        if not session_manager.exists(device_id):
            raise HTTPException(
                status_code=404,
                detail="Invalid device_id. Session not found."
            )

        try:
            device_data = session_manager.get(device_id)
            device_name = device_data.get("device_name")

            if not device_name:
                raise HTTPException(
                    status_code=400,
                    detail="Device not confirmed. Missing device_name."
                )

            # 🔍 RAG retrieval (FIXED)
            context = rag_service.query(device_name)
            print("DEBUG context:", context)

            if not context:
                return {"projects": []}

            # 🧠 Generate ideas
            projects = generator_service.run(context=context)

            return {"projects": projects}

        except Exception as e:
            print("🔥 FULL ERROR:", traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Idea generation failed: {str(e)}"
            )