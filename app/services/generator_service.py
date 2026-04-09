import os
import json
import re
from openai import OpenAI


class GeneratorService:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ GeneratorService initialized")

    # -------------------------------
    # ROBUST JSON PARSER (CRITICAL)
    # -------------------------------
    def _extract_json(self, text):
        if not text:
            return None

        # Remove markdown wrappers
        text = re.sub(r"```json|```", "", text).strip()

        # Try direct parse
        try:
            return json.loads(text)
        except:
            pass

        # Extract JSON block
        matches = re.findall(r'\{.*\}', text, re.DOTALL)

        for m in matches:
            try:
                cleaned = m.replace("'", '"')
                cleaned = re.sub(r',\s*}', '}', cleaned)
                cleaned = re.sub(r',\s*]', ']', cleaned)
                return json.loads(cleaned)
            except:
                continue

        print("❌ FINAL JSON PARSE FAILED")
        return None

    # -------------------------------
    # STEP 1: CLEAN CONTEXT
    # -------------------------------
    def _prepare_context(self, context):

        components = context.get("components", [])
        capabilities = context.get("capabilities", [])

        # Deduplicate
        components = list(set(components))

        # Prioritize important components
        priority_keywords = ["camera", "display", "battery", "sensor", "connectivity"]

        prioritized = []
        others = []

        for c in components:
            if any(k in c.lower() for k in priority_keywords):
                prioritized.append(c)
            else:
                others.append(c)

        components = prioritized[:5] + others[:5]

        capabilities = list(set(capabilities))[:5]

        return components, capabilities

    # -------------------------------
    # STEP 2: IDEA GENERATION
    # -------------------------------
    def _generate_ideas(self, components, capabilities):

        prompt = f"""
You are an expert DIY systems engineer.

DEVICE COMPONENTS:
{components}

DEVICE CAPABILITIES:
{capabilities}

Generate 5 HIGH-QUALITY DIY projects.

STRICT RULES:
- MUST use 2–3 REAL device components
- MUST include at least one external component
- MUST follow: sensor → trigger → action
- MUST be physically buildable
- NO vague ideas
- NO software-only ideas
- NO OS-level hacks

IMPORTANT:
- ONLY use components listed above
- DO NOT invent sensors
- External sensors allowed ONLY as external_components
- DO NOT rely on vague terms like "Sensor System"

OUTPUT STRICT JSON:
{{
  "ideas": [
    {{
      "title": "...",
      "description": "...",
      "components_used": ["..."],
      "external_components": ["..."]
    }}
  ]
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        content = response.choices[0].message.content.strip()

        print("\n🧠 IDEA RAW OUTPUT:\n", content)

        parsed = self._extract_json(content)
        return parsed if parsed else {"ideas": []}

    # -------------------------------
    # STEP 3: IDEA VALIDATION
    # -------------------------------
    def _validate_ideas(self, ideas, components, capabilities):

        prompt = f"""
You are a strict engineering reviewer.

DEVICE COMPONENTS:
{components}

DEVICE CAPABILITIES:
{capabilities}

IDEAS:
{json.dumps(ideas, indent=2)}

FILTER invalid ideas.

REJECT if:
- Uses non-existent components
- Invents hardware
- Vague or unrealistic
- Device not central

KEEP only realistic, grounded ideas.

OUTPUT JSON:
{{
  "ideas": [
    {{
      "title": "...",
      "description": "...",
      "components_used": ["..."],
      "external_components": ["..."]
    }}
  ]
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        print("\n🔍 VALIDATION RAW OUTPUT:\n", content)

        parsed = self._extract_json(content)
        return parsed if parsed else {"ideas": []}
    
    # -------------------------------
    # STEP 4: PROJECT GENERATION
    # -------------------------------
    def _generate_projects(self, ideas):

        prompt = f"""
    You are an expert DIY instructor.

    You are given project ideas:

    {json.dumps(ideas, indent=2)}

    Convert each idea into a REAL DIY project.

    REQUIREMENTS:
    - EXACTLY 4 steps per project
    - Steps must be clear, actionable, and realistic
    - Include at least one physical setup step
    - Avoid vague instructions

    DIFFICULTY RULES:
    - Easy → basic setup, no hardware modification
    - Medium → requires external components + setup
    - Hard → complex system integration

    OUTPUT STRICT JSON:

    {{
    "projects": [
        {{
        "title": "...",
        "difficulty": "Easy | Medium | Hard",
        "steps": {{
            "1": "...",
            "2": "...",
            "3": "...",
            "4": "..."
        }}
        }}
    ]
    }}
    """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        print("\n🧩 PROJECT RAW OUTPUT:\n", content)

        parsed = self._extract_json(content)

        if not parsed or "projects" not in parsed:
            print("⚠️ Project generation failed → fallback")

            # fallback: minimal conversion
            fallback = []
            for idea in ideas[:3]:
                fallback.append({
                    "title": idea.get("title", "DIY Project"),
                    "difficulty": "Medium",
                    "steps": {
                        "1": "Set up the device and required components.",
                        "2": "Connect external components as needed.",
                        "3": "Configure the system behavior.",
                        "4": "Test and refine the setup."
                    }
                })

            return fallback

        return parsed["projects"]

    # -------------------------------
    # MAIN PIPELINE
    # -------------------------------
    def run(self, context):

        print("\n🚀 GENERATOR PIPELINE STARTED\n")

        # STEP 1: Context
        components, capabilities = self._prepare_context(context)

        print("🧩 Components:", components[:3])
        print("⚙️ Capabilities:", capabilities[:3])

        # STEP 2: Generate Ideas
        ideas_data = self._generate_ideas(components, capabilities)
        ideas = ideas_data.get("ideas", [])

        if not ideas:
            print("⚠️ No ideas generated")
            return []

        # STEP 3: Validate Ideas
        validated_data = self._validate_ideas(ideas, components, capabilities)
        validated_ideas = validated_data.get("ideas", [])

        # 🔥 FALLBACK (CRITICAL)
        if not validated_ideas:
            print("⚠️ Validation failed → using raw ideas")
            validated_ideas = ideas[:3]

        print("✅ Final Ideas:", validated_ideas)

        # -------------------------------
        # STEP 4: PROJECT GENERATION
        # -------------------------------
        projects = self._generate_projects(validated_ideas)

        print("🏁 FINAL PROJECTS:", projects)

        return projects