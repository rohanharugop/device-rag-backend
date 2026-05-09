import os
import json
import re
from typing import List, Optional
from openai import OpenAI
from pinecone import Pinecone
from app.tools.web_search import web_search

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))


# ── Helpers ──────────────────────────────────────────────────

def normalize_device_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def normalize_instruction(instruction) -> str:
    if isinstance(instruction, list):
        return " ".join(
            f"{i}. {str(item).strip()}"
            for i, item in enumerate(instruction, 1) if item
        )
    if isinstance(instruction, str):
        return instruction.strip()
    return str(instruction).strip()


def extract_json(text: str) -> Optional[dict]:
    try:
        text = re.sub(r"```json|```", "", text).strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None


def call_llm(prompt: str, retries: int = 3) -> dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No markdown, no explanation."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            raw = res.choices[0].message.content
            parsed = extract_json(raw)
            if parsed:
                return parsed
        except Exception as e:
            last_error = e
    raise RuntimeError(f"LLM failed after {retries} attempts. Last error: {last_error}")


# ── Pinecone ─────────────────────────────────────────────────

def fetch_device_specs(device_name: str) -> List[str]:
    namespace = normalize_device_name(device_name)
    query_text = f"hardware specs sensors capabilities of {device_name}"
    METADATA_TEXT_FIELDS = ["text", "capabilities", "components", "pwa_capability_tags"]

    try:
        embedding = (
            client.embeddings.create(input=query_text, model="text-embedding-ada-002")
            .data[0].embedding
        )
    except Exception:
        return []

    try:
        results = index.query(
            vector=embedding, top_k=5,
            include_metadata=True, namespace=namespace,
        )
        matches = results.get("matches", [])
        if not matches:
            return []

        raw_specs = []
        for m in matches:
            meta = m.get("metadata", {})
            if not meta:
                continue
            parts = []
            for field in METADATA_TEXT_FIELDS:
                val = meta.get(field)
                if not val:
                    continue
                if isinstance(val, str) and val.startswith("["):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            val = ", ".join(str(v) for v in parsed)
                    except json.JSONDecodeError:
                        pass
                parts.append(f"{field}: {val}")
            extracted = "\n".join(parts)
            if extracted.strip():
                raw_specs.append(extracted)
        return raw_specs
    except Exception:
        return []


# ── Planner ──────────────────────────────────────────────────

def generate_plan(project: dict, device: dict, specs: List[str], feedback=None) -> dict:
    feedback_str = ""
    if feedback:
        feedback_str = "\n".join(f"- {s}" for s in feedback) if isinstance(feedback, list) else str(feedback)

    specs_str = "\n".join(specs) if specs else "No specs retrieved."

    prompt = f"""You are designing a DIY project for a NON-TECHNICAL USER.

DEVICE: {device['device_name']}
DEVICE SPECS: {specs_str}
PROJECT: {json.dumps(project, indent=2)}
FEEDBACK FROM PREVIOUS ATTEMPT: {feedback_str if feedback_str else "None — this is the first attempt."}

RULES:
- No coding, APIs, or frameworks
- Use real, named apps where applicable
- Each step must be a single executable action
- Do NOT create a step whose only action is opening an app already launched in the previous step

MANDATORY STEP ORDER:
1. SOFTWARE FIRST: installs, account creation, permissions, configuration
2. PHYSICAL SETUP SECOND: positioning, mounting (only after software ready)
3. POWER MANAGEMENT: alongside or just after physical placement
4. TESTING LAST: always the final step

Return JSON:
{{
  "goal": "...",
  "plan": ["step1", "step2", ...],
  "sensor_used": ["camera", "accelerometer", ...]
}}"""

    return call_llm(prompt)


def critique_plan(plan: dict) -> dict:
    prompt = f"""You are reviewing a step-by-step DIY plan for a non-technical user.

PLAN: {json.dumps(plan.get("plan", []), indent=2)}
GOAL: {plan.get("goal", "")}

Evaluate on:
1. Vague or non-actionable steps?
2. Steps combining multiple actions?
3. Technical steps (coding, CLI)?
4. Beginner-followable?
5. Correct order: software → physical → power → testing?
6. Testing is the LAST step?

CALIBRATION: Only mark valid=false for CONCRETE, SPECIFIC problems.

Return JSON:
{{
  "valid": true or false,
  "issues": ["issue 1", ...],
  "suggestions": ["fix 1", ...]
}}"""

    return call_llm(prompt)


def run_plan_loop(project: dict, device: dict) -> dict:
    """Runs planner + critic loop. Returns the accepted plan dict."""
    specs = fetch_device_specs(device["device_name"])
    feedback = None
    final_plan = None

    for attempt in range(1, 4):
        try:
            plan = generate_plan(project, device, specs, feedback)
        except RuntimeError as e:
            break

        try:
            critique = critique_plan(plan)
        except RuntimeError:
            final_plan = plan
            break

        if critique.get("valid"):
            final_plan = plan
            break
        else:
            feedback = critique.get("suggestions")

    return final_plan or plan


# ── Step Executor ─────────────────────────────────────────────

def extract_opening_phrases(history: list) -> list:
    forbidden = []
    REPEAT_PATTERNS = [
        "open the ", "tap on the settings", "tap the settings",
        "ensure your iphone is connected", "make sure your iphone is connected",
        "ensure the app is", "make sure the app is",
    ]
    for h in history:
        instruction_text = normalize_instruction(h.get("instruction", ""))
        sub_steps = re.split(r'\d+\.\s+', instruction_text)
        for sub in sub_steps:
            sub_lower = sub.strip().lower()
            for pattern in REPEAT_PATTERNS:
                if sub_lower.startswith(pattern):
                    forbidden.append(sub.strip()[:100])
                    break
    return list(dict.fromkeys(forbidden))


def critique_step(plan_goal: str, device_name: str, history: list,
                  step_text: str, step_result: dict, tool_data) -> dict:
    history_full = [
        {
            "step_number": h.get("step_number"),
            "step_title": h["step"],
            "full_instruction": normalize_instruction(h["instruction"]),
        }
        for h in history
    ]

    prompt = f"""You are reviewing a single DIY instruction step for a non-technical user.

PROJECT GOAL: {plan_goal}
DEVICE: {device_name}
CURRENT STEP: {step_text}
GENERATED INSTRUCTION: {step_result.get("instruction")}
TOOL DATA: {tool_data}
HISTORY: {json.dumps(history_full, indent=2)}

EVALUATION CRITERIA:
1. SCOPE — covers ONLY the current step?
2. REDUNDANCY — repeats an exact sub-step from history? (must quote both sides to fail)
3. OPENING LINE — fails only if literally begins with "Open the [app]" done in prior step
4. FAITHFULNESS — contradicts tool data?
5. CLARITY — impossible to follow?

CALIBRATION: Default to valid=true. When in doubt, pass.

Return JSON:
{{
  "valid": true or false,
  "issues": ["DUPLICATE: '[exact text]' repeats '[exact history text]'"],
  "fix": "corrected instruction if invalid, else empty string"
}}"""

    return call_llm(prompt)


def should_use_tool(step: str, device_name: str) -> bool:
    prompt = f"""Does this DIY step require searching for real-world app recommendations or current information?
STEP: {step}
DEVICE: {device_name}
Reply ONLY: {{"use_tool": true}} or {{"use_tool": false}}"""
    try:
        return bool(call_llm(prompt).get("use_tool", False))
    except Exception:
        return False


def execute_single_step(plan: dict, device: dict, history: list, step: str) -> dict:
    """
    Executes one step with the critic retry loop.
    Returns {"instruction": "...", "tips": [...], "video_url": "..."}
    """
    tool_data = None
    if should_use_tool(step, device["device_name"]):
        sensors = plan.get("sensor_used", [])
        query = f"{step} using {', '.join(sensors) or 'sensors'} on {device['device_name']}"
        tool_data = web_search(query)

    covered_topics = [h["step"] for h in history]
    covered_instructions = [
        {"step": h["step"], "full_instruction": normalize_instruction(h["instruction"])}
        for h in history
    ]
    forbidden_phrases = extract_opening_phrases(history)
    app_already_opened = any(
        "open" in normalize_instruction(h.get("instruction", "")).lower()
        for h in history
    )

    failure_reason = ""
    last_critic_fix = ""
    result = {}

    for attempt in range(1, 4):
        # On attempt 2+, apply critic's fix directly
        if attempt >= 2 and last_critic_fix:
            result["instruction"] = normalize_instruction(last_critic_fix)
            critique = critique_step(
                plan.get("goal"), device["device_name"],
                history, step, result, tool_data
            )
            if critique.get("valid"):
                return _attach_video(result, step, device["device_name"], len(history) + 1)
            last_critic_fix = critique.get("fix", "")
            failure_reason = "; ".join(critique.get("issues", []))
            if last_critic_fix:
                failure_reason += f"\nSuggested fix: {last_critic_fix}"
            continue

        forbidden_block = ""
        if forbidden_phrases:
            formatted = "\n".join(f'  - "{p}"' for p in forbidden_phrases)
            forbidden_block = f"\nFORBIDDEN PHRASES (do NOT repeat):\n{formatted}"

        app_open_note = ""
        if app_already_opened:
            app_open_note = (
                "\nAPP STATE: App already opened. Do NOT start with 'Open the app'."
            )

        prompt = f"""Write instructions for ONE specific DIY step. User is a complete beginner.

DEVICE: {device['device_name']}
PROJECT GOAL: {plan.get('goal')}

CURRENT STEP (your ONLY focus):
{step}

WEB SEARCH DATA: {tool_data}
COMPLETED STEPS (topics): {json.dumps(covered_topics, indent=2)}
COMPLETED STEPS (full text): {json.dumps(covered_instructions, indent=2)}
{forbidden_block}{app_open_note}
{f"REASON LAST ATTEMPT FAILED (MUST fix): {failure_reason}" if failure_reason else ""}

RULES:
- Cover ONLY the current step
- No coding or APIs
- instruction MUST be a single string with numbered sub-steps
- Be specific and beginner-friendly

Return JSON:
{{
  "instruction": "1. Do this. 2. Then this. 3. Finally this.",
  "tips": ["tip1", "tip2"]
}}"""

        result = call_llm(prompt)
        result["instruction"] = normalize_instruction(result.get("instruction", ""))

        critique = critique_step(
            plan.get("goal"), device["device_name"],
            history, step, result, tool_data
        )

        if critique.get("valid"):
            return _attach_video(result, step, device["device_name"], len(history) + 1)

        last_critic_fix = critique.get("fix", "")
        failure_reason = "; ".join(critique.get("issues", []))
        if last_critic_fix:
            failure_reason += f"\nSuggested fix: {last_critic_fix}"

    # Exhausted retries — use last fix or last result
    if last_critic_fix:
        result["instruction"] = normalize_instruction(last_critic_fix)
    return _attach_video(result, step, device["device_name"], len(history) + 1)


def _attach_video(result: dict, step: str, device_name: str, step_number: int) -> dict:
    """Placeholder — swap in real YouTube search later."""
    result["video_url"] = None  # replace with video_recommendation_agent() when ready
    return result


# ── Issue Diagnosis ───────────────────────────────────────────

def diagnose_issue(step: str, device_name: str, plan_goal: str, issue_detail: str) -> dict:
    prompt = f"""A beginner user is stuck on this DIY step.

USER'S ISSUE: {issue_detail}
STEP: {step}
DEVICE: {device_name}
PROJECT GOAL: {plan_goal}

Return JSON:
{{
  "diagnosis": "clear explanation of what went wrong",
  "solutions": ["solution 1", "solution 2", ...]
}}"""

    return call_llm(prompt)