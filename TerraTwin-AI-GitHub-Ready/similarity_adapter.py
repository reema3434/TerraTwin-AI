from pathlib import Path
from main import compare, CONDITIONS, FEATURES, DATA_FILE
from mission_classifier import normalize_target

UI_MISSION_TO_CONDITION = {
    "Mobility": "mobility",
    "Navigation": "navigation",
    "Robotic Operations": "robotic_operations",
    "navigation_mobility": "mobility",
    "maneuverability": "navigation",
    "positioning_stationing": "robotic_operations",
    "mobility": "mobility",
    "navigation": "navigation",
    "robotic_operations": "robotic_operations",
}

UI_PARAM_MAP = {
    "slope_deg": "slope_deg",
    "roughness_m": "roughness_m",
    "local_relief_m": "local_relief_m",
    "slope_std_deg": "slope_std_deg",
    "flat_fraction": "flat_fraction",
    "flat_area_pct": "flat_fraction",  # Maps legacy UI key to official flat_fraction
}

FEATURE_DISPLAY_NAMES = {
    "slope_deg": "Mean slope (°)",
    "roughness_m": "Mean roughness (m)",
    "local_relief_m": "Mean local relief (m)",
    "slope_std_deg": "Slope variability (°)",
    "flat_fraction": "Flat fraction",
    "flat_area_pct": "Flat fraction",
}


def run_similarity_comparison(
    target_body: str = "Moon",
    target_region: str = "Connecting_Ridge",
    mission_type: str = "Mobility",
    custom_features: list = None,
    csv_path: str = str(DATA_FILE),
) -> dict:
    """
    Calls Member 3's official main.py `compare()` function using terrain_data.csv
    and computes all three condition scores for comparison.
    """
    body, region = normalize_target(target_body, target_region)
    condition_key = UI_MISSION_TO_CONDITION.get(mission_type)

    if condition_key in CONDITIONS:
        payload = compare(
            csv_path=csv_path,
            target_body=body,
            target_region=region,
            condition=condition_key,
        )
    else:
        cleaned_features = []
        for f_name in (custom_features or FEATURES):
            mapped = UI_PARAM_MAP.get(f_name)
            if mapped in FEATURES and mapped not in cleaned_features:
                cleaned_features.append(mapped)
        if not cleaned_features:
            cleaned_features = ["slope_deg", "roughness_m", "local_relief_m"]

        payload = compare(
            csv_path=csv_path,
            target_body=body,
            target_region=region,
            selected_features=cleaned_features,
        )

    # Calculate all 3 condition scores for the Dashboard expander
    condition_labels = {
        "mobility": "Mobility (Navigation & Mobility)",
        "navigation": "Navigation (Maneuverability)",
        "robotic_operations": "Robotic Operations (Positioning & Stationing)",
    }
    all_condition_scores = {}
    for c_key, c_label in condition_labels.items():
        c_res = compare(
            csv_path=csv_path,
            target_body=body,
            target_region=region,
            condition=c_key,
        )
        best_c = c_res["best_match"]
        all_condition_scores[f"{c_label} — {best_c['region']}"] = round(
            float(best_c["overall_similarity_score"]), 2
        )

    return {
        "payload": payload,
        "condition_scores": all_condition_scores,
    }
