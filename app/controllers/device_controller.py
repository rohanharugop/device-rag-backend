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
from app.db.project_store import create_project, get_project
from app.db.project_store import create_project, get_project, update_project, mark_complete
from app.services.agent_service import run_plan_loop, execute_single_step, diagnose_issue

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
    def _clean_specs(components: list, capabilities: list) -> tuple:
        """
        Deduplicates by component type and title-cases for cleaner UI display.
        Keeps only the first (most concise) entry per component type.
        Does not modify any retrieval or storage logic.
        """
        def clean_components(items: list) -> list:
            seen_types = {}
            for item in items:
                normalized = str(item).strip().title()
                # Extract the component type — everything before the first "("
                type_key = normalized.split("(")[0].strip().lower()
                if not type_key:
                    continue
                # Keep the shortest entry per type (most concise)
                if type_key not in seen_types:
                    seen_types[type_key] = normalized
                else:
                    if len(normalized) < len(seen_types[type_key]):
                        seen_types[type_key] = normalized
            return list(seen_types.values())[:8]  # hard cap at 8

        def clean_capabilities(items: list) -> list:
            seen = set()
            cleaned = []
            for item in items:
                normalized = str(item).strip().title()
                key = normalized.lower()
                if key and key not in seen:
                    seen.add(key)
                    cleaned.append(normalized)
            return cleaned

        return clean_components(components), clean_capabilities(capabilities)
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
            components, capabilities = DeviceController._clean_specs(
                data.get("components", []),
                data.get("capabilities", [])
            )
            return {
                "device_id": device_id,
                "components": components,
                "capabilities": capabilities,
                "sources": ["cache"]
            }

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
        components, capabilities = DeviceController._clean_specs(components, capabilities)
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
        
    @staticmethod
    def check_pwa_compatibility(device_id: str, software_capabilities: list):

        from app.services.requirement_mapper_agent import RequirementMapperAgent
        from app.services.rag_service import RAGService

        if not session_manager.exists(device_id):
            raise HTTPException(404, "Invalid device_id")

        device_data = session_manager.get(device_id)
        device_name = device_data.get("device_name")

        if not device_name:
            raise HTTPException(400, "Device not confirmed")

        rag_service = RAGService()
        context = rag_service.query(device_name)

        components = context.get("components", [])
        capabilities = context.get("capabilities", [])

        # 🔥 Combine hardware signals safely
        device_hw = components + capabilities
        device_sw = software_capabilities or []

        templates = ["security_cam", "dashboard", "media_server"]

        agent = RequirementMapperAgent()
        results = agent.evaluate_all(templates, device_hw, device_sw)

        # 🔥 Save compatible templates in session (IMPORTANT)
        valid_templates = [r["template"] for r in results if r["compatible"]]

        session_manager.update(device_id, {
            "valid_templates": valid_templates
        })

        return {
            "device_id": device_id,
            "results": results,
            "valid_templates": valid_templates
        }
    
    @staticmethod
    def generate_pwa(device_id: str):

        from app.services.pwa_generator_service import PWAGeneratorService

        if not session_manager.exists(device_id):
            raise HTTPException(404, "Invalid device_id")

        device_data = session_manager.get(device_id)

        device_name = device_data.get("device_name")
        valid_templates = device_data.get("valid_templates", [])

        if not device_name:
            raise HTTPException(400, "Device not confirmed")

        if not valid_templates:
            return {
                "message": "No compatible PWAs found. Please check device capabilities."
            }

        # 🔥 pick first valid template (safe default)
        template = valid_templates[0]

        generator = PWAGeneratorService()

        config = {
            "device_name": device_name,
            "capabilities": device_data.get("capabilities", [])
        }

        zip_path = generator.generate(template, device_id, config)

        return {
            "pwa_type": template,
            "download_url": zip_path
        }
    
    @staticmethod
    def run_project(device_id: str, device_name: str, title: str, difficulty: str, steps: dict):
        if not session_manager.exists(device_id):
            raise HTTPException(404, "Invalid device_id")

        steps_list = [steps[k] for k in sorted(steps.keys(), key=lambda x: int(x))]

        project = {
                "title": title,
                "difficulty": difficulty,
                "device_id": device_id,
                "device_name": device_name,
            }
        device = {"device_name": device_name}

            # Run planner + critic loop
        plan = run_plan_loop(project, device)
        plan_steps = plan.get("plan", [])
        plan_steps = [
            s if s.strip().endswith(".") else s.strip() + "."
            for s in plan_steps
        ]

            # Persist to SQLite
        project_id = create_project(device_id, device_name)
        update_project(project_id,
                plan=plan,
                steps=plan_steps,
                current_step=0,
                history=[],
                step_videos=[None] * len(plan_steps),
                status="planned"
            )

        return {
        "project_id": project_id,
        "title": title,
        "goal": plan.get("goal"),
        "plan": plan_steps,
        "total_steps": len(plan_steps),
        "status": "planned",
        "video_url": plan.get("video_url"),
        "mermaid_chart": plan.get("mermaid_chart", ""),  # ← reads from LLM-generated chart
    }
    
    @staticmethod
    def next_step(project_id: str):
        project = get_project(project_id)
        if not project:
            raise HTTPException(404, "Project not found")
        if project["status"] == "complete":
            return {"status": "complete", "message": "Project already finished"}

        i = project["current_step"]
        steps = project["steps"]

        if i >= len(steps):
            mark_complete(project_id)
            return {"status": "complete", "message": "All steps done"}

        step = steps[i]
        history = project["history"] or []
        plan = project["plan"]
        device = {"device_name": project["device_name"]}

        result = execute_single_step(plan, device, history, step)

        return {
            "project_id": project_id,
            "step_number": i + 1,
            "total_steps": len(steps),
            "step_title": step,
            "instruction": result.get("instruction"),
            "tips": result.get("tips", []),
            "video_url": result.get("video_url"),
            "status": "in_progress"
        }


    @staticmethod
    def submit_step(project_id: str, action: str, issue_detail: str = None):
        project = get_project(project_id)
        if not project:
            raise HTTPException(404, "Project not found")

        i = project["current_step"]
        steps = project["steps"]
        step = steps[i]

        if action == "done":
            # Re-execute to get the instruction for history
            # (or you can cache last result — see note below)
            history = project["history"] or []
            plan = project["plan"]
            device = {"device_name": project["device_name"]}
            result = execute_single_step(plan, device, history, step)

            updated_history = history + [{
                "step_number": i + 1,
                "step": step,
                "instruction": result.get("instruction", ""),
            }]
            new_step = i + 1

            if new_step >= len(steps):
                update_project(project_id,
                    current_step=new_step,
                    history=updated_history,
                    status="complete"
                )
                return {"status": "complete", "message": "Project complete!"}

            update_project(project_id,
                current_step=new_step,
                history=updated_history
            )
            return {"status": "advanced", "next_step": new_step + 1}

        elif action == "issue":
            if not issue_detail:
                raise HTTPException(400, "issue_detail required when action is 'issue'")
            plan = project["plan"]
            diagnosis = diagnose_issue(
                step=step,
                device_name=project["device_name"],
                plan_goal=plan.get("goal", ""),
                issue_detail=issue_detail
            )
            return {
                "status": "issue_diagnosed",
                "step_number": i + 1,
                "diagnosis": diagnosis.get("diagnosis"),
                "solutions": diagnosis.get("solutions", [])
            }

        raise HTTPException(400, "action must be 'done' or 'issue'")