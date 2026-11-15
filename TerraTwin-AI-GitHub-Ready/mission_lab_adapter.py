import os
from groq import Groq

MODEL_NAME = "llama-3.3-70b-versatile"

# Official Mission Test Lab Hybrid Classification Results (75 m resolution, Member 4)
MISSION_LAB_DATA = {
    "AlUla": {
        "body": "Earth",
        "low_pct": 56.99,
        "medium_pct": 17.60,
        "high_pct": 25.41,
        "slope_deg": 9.6595,
        "roughness_m": 37.0471,
        "local_relief_m": 91.5205,
        "slope_std_deg": 9.7672,
        "flat_fraction": 0.006430,
        "bounds": [[26.45, 37.75], [26.75, 38.10]],
        "crs": "EPSG:4326",
        "raster_url": "maps/AlUla_difficulty_map.tif",
    },
    "Harrat_Khaybar": {
        "body": "Earth",
        "low_pct": 83.02,
        "medium_pct": 9.24,
        "high_pct": 7.74,
        "slope_deg": 5.1716,
        "roughness_m": 18.3488,
        "local_relief_m": 51.2506,
        "slope_std_deg": 5.5823,
        "flat_fraction": 0.016821,
        "bounds": [[25.55, 39.80], [25.90, 40.15]],
        "crs": "EPSG:4326",
        "raster_url": "maps/Harrat_Khaybar_difficulty_map.tif",
    },
    "Connecting_Ridge": {
        "body": "Moon",
        "low_pct": 34.29,
        "medium_pct": 35.09,
        "high_pct": 30.62,
        "slope_deg": 12.0150,
        "roughness_m": 41.2632,
        "local_relief_m": 120.7711,
        "slope_std_deg": 5.5462,
        "flat_fraction": 0.000000,
        "bounds": [[-89.60, -45.00], [-89.40, 45.00]],
        "crs": "Lunar_South_Pole_Stereographic",
        "raster_url": "maps/Connecting_Ridge_difficulty_map.tif",
    },
    "Athabasca_Valles": {
        "body": "Mars",
        "low_pct": 84.11,
        "medium_pct": 6.05,
        "high_pct": 9.84,
        "slope_deg": 5.3857,
        "roughness_m": 18.9631,
        "local_relief_m": 54.3832,
        "slope_std_deg": 7.4509,
        "flat_fraction": 0.213888,
        "bounds": [[8.50, 154.50], [10.00, 156.00]],
        "crs": "Mars_2000_IAU",
        "raster_url": "maps/Athabasca_Valles_difficulty_map.tif",
    },
}

HYBRID_THRESHOLDS = {
    "resolution": "75 m (16 × 16 km study areas)",
    "slope_thresholds_deg": [10.0, 15.0],
    "roughness_p65_m": 31.28,
    "roughness_p90_m": 68.30,
    "rules": {
        "Low (🟢)": "Slope < 10° AND Roughness < 31.28 m (P65)",
        "Medium (🟡)": "Remaining valid pixels between Low and High thresholds",
        "High (🔴)": "Slope >= 15° OR Roughness >= 68.30 m (P90)",
    },
}


def get_mission_lab_assessment(earth_region: str, target_region: str) -> dict:
    e_reg = earth_region if earth_region in MISSION_LAB_DATA else "AlUla"
    t_reg = target_region if target_region in MISSION_LAB_DATA else "Connecting_Ridge"

    e_info = MISSION_LAB_DATA[e_reg]
    t_info = MISSION_LAB_DATA[t_reg]

    fallback_exp = (
        f"Using the 75 m Hybrid Classification (Slope 10°/15°; Roughness P65=31.28 m, P90=68.30 m), "
        f"**{e_reg}** exhibits **{e_info['low_pct']}% Low**, **{e_info['medium_pct']}% Medium**, and "
        f"**{e_info['high_pct']}% High** terrain difficulty, compared to **{t_reg}** ({t_info['body']}) "
        f"with **{t_info['low_pct']}% Low**, **{t_info['medium_pct']}% Medium**, and **{t_info['high_pct']}% High**. "
        f"These distributions reflect relative topographic difficulty and are not physical rover simulations."
    )

    api_key = os.environ.get("GROQ_API_KEY", "")
    ai_exp = fallback_exp
    if api_key and "ضعي_مفتاح" not in api_key:
        prompt = f"""
        You are an AI terrain difficulty analyst for TerraTwin AI Mission Test Lab.
        In 2 concise sentences, compare the terrain difficulty classification of '{e_reg}' (Earth) and '{t_reg}' ({t_info['body']}) using ONLY these exact percentages:
        - {e_reg}: Low={e_info['low_pct']}%, Medium={e_info['medium_pct']}%, High={e_info['high_pct']}% (Mean Slope={e_info['slope_deg']}°, Mean Roughness={e_info['roughness_m']}m)
        - {t_reg}: Low={t_info['low_pct']}%, Medium={t_info['medium_pct']}%, High={t_info['high_pct']}% (Mean Slope={t_info['slope_deg']}°, Mean Roughness={t_info['roughness_m']}m)
        - Hybrid rules: Low (Slope<10° & Roughness<31.28m), High (Slope>=15° or Roughness>=68.30m).
        Note that this is a relative terrain difficulty assessment, not a physical rover simulation.
        """
        try:
            client = Groq(api_key=api_key, timeout=8.0)
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=0.2,
                max_tokens=160,
            )
            ai_exp = res.choices[0].message.content.strip()
        except Exception:
            ai_exp = fallback_exp

    return {
        "recommended_earth_region": e_reg,
        "target_planetary_region": t_reg,
        "earth_stats": e_info,
        "target_stats": t_info,
        "all_regions": MISSION_LAB_DATA,
        "thresholds": HYBRID_THRESHOLDS,
        "ai_explanation": ai_exp,
    }
