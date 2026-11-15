from mission_classifier import classify_user_mission, normalize_target
from similarity_adapter import (
    run_similarity_comparison,
    UI_PARAM_MAP,
    FEATURE_DISPLAY_NAMES,
)
from results_explainer import (
    build_feature_justifications,
    generate_scientific_explanation,
)
from mission_lab_adapter import get_mission_lab_assessment


def run_full_analysis(
    target_body: str = "Moon",
    target_region: str = "Connecting_Ridge",
    mission_type: str = "Mobility",
    parameters: list = None,
    user_query: str = None,
    csv_path: str = "terrain_data.csv",
) -> dict:
    """
    Main integration pipeline connecting:
    User Input -> AI Mission Classifier -> Member 3 Similarity Engine -> AI Explainer -> Mission Test Lab
    Returns the exact dictionary format required by `app.py` (`st.session_state["analysis_result"]`).
    """
    classification = None
    if user_query and str(user_query).strip():
        classification = classify_user_mission(user_query, fallback_body=target_body)
        target_body = classification["target_body"]
        target_region = classification["target_region"]
        mission_type = classification["ui_mission"]

    body, region = normalize_target(target_body, target_region)

    # Run Member 3's Similarity Engine
    sim_out = run_similarity_comparison(
        target_body=body,
        target_region=region,
        mission_type=mission_type,
        custom_features=parameters,
        csv_path=csv_path,
    )
    payload = sim_out["payload"]
    best = payload["best_match"]
    target = payload["target"]

    # Build feature justifications & overall scientific explanation
    ui_features = parameters or payload["selected_features"]
    feature_scores = build_feature_justifications(payload, ui_features)
    mission_label = mission_type or "Custom Terrain Parameters"
    overall_justification = generate_scientific_explanation(payload, mission_label)

    # Build feature_comparison rows matching app.py table columns
    comparison_rows = []
    for f_key in payload["selected_features"]:
        d = best["feature_details"][f_key]
        comparison_rows.append({
            "feature": FEATURE_DISPLAY_NAMES.get(f_key, f_key),
            "earth": round(float(d["earth_value"]), 4),
            "target": round(float(d["target_value"]), 4),
            "absolute_difference": round(float(d["raw_difference"]), 4),
            "normalized_difference": round(float(d["normalized_difference"]), 4),
            "similarity": round(float(d["similarity_pct"]), 2),
            "weight": round(float(d["weight"]), 4),
        })

    # Load Mission Test Lab assessment for the top-ranked Earth region
    lab_assessment = get_mission_lab_assessment(
        earth_region=best["region"],
        target_region=target["region"],
    )

    return {
        "total_similarity_percentage": round(float(best["overall_similarity_score"]), 2),
        "best_earth_region": best["region"],
        "target_body": target["body"],
        "target_region": target["region"],
        "mission_type": mission_label,
        "selected_features": payload["selected_features"],
        "ai_classification": classification,
        "feature_scores": feature_scores,
        "feature_comparison": comparison_rows,
        "condition_scores": sim_out["condition_scores"],
        "all_candidates": payload.get("all_candidates", [best]),
        "overall_justification": overall_justification,
        "raster": {
            "url": lab_assessment["earth_stats"]["raster_url"],
            "bounds": lab_assessment["earth_stats"]["bounds"],
            "crs": lab_assessment["earth_stats"]["crs"],
        },
        "mission_lab": lab_assessment,
    }
