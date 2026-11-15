import os
import json
from groq import Groq
from similarity_adapter import UI_PARAM_MAP, FEATURE_DISPLAY_NAMES

MODEL_NAME = "llama-3.3-70b-versatile"


def build_feature_justifications(payload: dict, requested_features: list = None) -> dict:
    """
    Build grounded justifications for each feature directly from Member 3's `feature_details`.
    """
    best = payload["best_match"]
    target = payload["target"]
    details = best["feature_details"]

    features_to_process = requested_features or payload["selected_features"]
    feature_scores = {}

    for req_feat in features_to_process:
        eng_feat = UI_PARAM_MAP.get(req_feat, req_feat)
        if eng_feat not in details:
            continue
        d = details[eng_feat]
        pct = round(float(d["similarity_pct"]), 2)
        e_val = round(float(d["earth_value"]), 4)
        t_val = round(float(d["target_value"]), 4)
        diff = round(float(d["raw_difference"]), 4)
        w_pct = round(float(d["weight"]) * 100, 1)

        text = (
            f"{best['region']} = {e_val} vs. {target['region']} = {t_val} "
            f"(|Δ| = {diff}, equal weight = {w_pct}%), resulting in {pct:.2f}% feature similarity."
        )
        feature_scores[req_feat] = {
            "percentage": pct,
            "justification": text,
        }
        # Also populate under official engine key so UI always finds it
        feature_scores[eng_feat] = {
            "percentage": pct,
            "justification": text,
        }

    return feature_scores


def generate_scientific_explanation(payload: dict, mission_label: str) -> str:
    """
    Stage 3: Generate AI explanation grounded strictly in Member 3's computed output.
    """
    best = payload["best_match"]
    target = payload["target"]
    score = round(float(best["overall_similarity_score"]), 2)
    details = best["feature_details"]

    ranked_feats = sorted(
        details.items(),
        key=lambda item: item[1]["similarity_pct"],
        reverse=True,
    )
    strongest_feat, strongest_data = ranked_feats[0]
    weakest_feat, weakest_data = ranked_feats[-1]

    fallback = (
        f"**{best['region']}** ranked #1 among the Saudi candidate regions as a terrain analog for "
        f"**{target['region']}** ({target['body']}) under the **{mission_label}** mode with an overall "
        f"similarity score of **{score:.2f}%**. The highest contributing feature was `{strongest_feat}` "
        f"({strongest_data['similarity_pct']:.2f}% similarity: {best['region']}={strongest_data['earth_value']} "
        f"vs. {target['region']}={strongest_data['target_value']}), whereas `{weakest_feat}` recorded "
        f"{weakest_data['similarity_pct']:.2f}% similarity. Note: High topographic similarity supports "
        f"earth-based analog testing but does not guarantee actual planetary rover operational safety."
    )

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or "ضعي_مفتاح" in api_key:
        return fallback

    prompt = f"""
    You are a planetary geomorphology expert for TerraTwin AI.
    Write a clear 3-sentence scientific explanation of these exact similarity results:
    - Target Planetary Region: {target['region']} ({target['body']})
    - Mission Mode: {mission_label}
    - Selected Features: {payload['selected_features']}
    - Winning Saudi Region: {best['region']} (Overall Similarity Score: {score:.2f}%)
    - All Candidates Ranked: {[{'region': c['region'], 'score': round(c['overall_similarity_score'], 2)} for c in payload.get('all_candidates', [best])]}
    - Feature Details for {best['region']}: {json.dumps(details)}

    Requirements:
    1. State clearly why {best['region']} ranked #1 with {score:.2f}% similarity for {target['region']}.
    2. Cite the exact feature values and similarity percentages that contributed most (and least) to this score.
    3. Explicitly note that terrain similarity is a preliminary analog metric and does not guarantee rover safety.
    4. Do NOT invent any numbers outside the provided data.
    """
    try:
        client = Groq(api_key=api_key, timeout=8.0)
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
            temperature=0.2,
            max_tokens=200,
        )
        output_text = res.choices[0].message.content.strip()
        if best["region"].lower() not in output_text.lower():
            return fallback
        return output_text
    except Exception:
        return fallback
