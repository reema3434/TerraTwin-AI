import os
import json
from groq import Groq

MODEL_NAME = "openai/gpt-oss-120b"

ALLOWED_MISSION_TYPES = {
    "navigation_mobility": "Mobility",
    "maneuverability": "Navigation",
    "positioning_stationing": "Robotic Operations",
}

ALLOWED_TARGETS = {
    "Moon": "Connecting_Ridge",
    "Mars": "Athabasca_Valles",
}


def normalize_target(target_body: str, target_region: str = None) -> tuple:
    """Validate celestial body and map region to the 4 official study regions."""
    body = "Mars" if str(target_body).strip().lower() == "mars" else "Moon"
    valid_region = ALLOWED_TARGETS[body]
    return body, valid_region


def classify_user_mission(user_query: str, fallback_body: str = "Moon") -> dict:
    """
    Stage 1: Interpret user natural-language request into validated structured JSON:
    {"mission_type": ..., "target_body": ..., "target_region": ...}
    """
    body, default_region = normalize_target(fallback_body)
    api_key = os.environ.get("GROQ_API_KEY", "")

    if not user_query or not str(user_query).strip() or not api_key or "ضعي_مفتاح" in api_key:
        return {
            "mission_type": "navigation_mobility",
            "ui_mission": "Mobility",
            "engine_condition": "mobility",
            "target_body": body,
            "target_region": default_region,
            "is_fallback": True,
        }

    prompt = f"""
    You are the AI Mission Understanding module for TerraTwin AI.
    Analyze the user request and return ONLY a raw JSON object with these 3 keys:
    1. "mission_type": Strictly ONE from ["navigation_mobility", "maneuverability", "positioning_stationing"]
       - "navigation_mobility": movement, driving, traversability, general mobility.
       - "maneuverability": turning, maneuvering, negotiating uneven surfaces.
       - "positioning_stationing": stationing, landing, base stability, flat terrain.
    2. "target_body": Strictly ONE from ["Moon", "Mars"]
    3. "target_region": "Connecting_Ridge" if Moon, or "Athabasca_Valles" if Mars.

    User request: {user_query}
    """
    try:
        client = Groq(api_key=api_key, timeout=8.0)
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
            temperature=0.0,
            max_tokens=100,
        )
        raw = res.choices[0].message.content.strip()
        if "{" in raw and "}" in raw:
            raw = raw[raw.find("{"):raw.rfind("}") + 1]
        data = json.loads(raw)

        m_type = data.get("mission_type")
        if m_type not in ALLOWED_MISSION_TYPES:
            m_type = "navigation_mobility"

        t_body, t_region = normalize_target(data.get("target_body", body))
        engine_map = {
            "navigation_mobility": "mobility",
            "maneuverability": "navigation",
            "positioning_stationing": "robotic_operations",
        }
        return {
            "mission_type": m_type,
            "ui_mission": ALLOWED_MISSION_TYPES[m_type],
            "engine_condition": engine_map[m_type],
            "target_body": t_body,
            "target_region": t_region,
            "is_fallback": False,
        }
    except Exception:
        return {
            "mission_type": "navigation_mobility",
            "ui_mission": "Mobility",
            "engine_condition": "mobility",
            "target_body": body,
            "target_region": default_region,
            "is_fallback": True,
        }
