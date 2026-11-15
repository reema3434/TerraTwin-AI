from pathlib import Path
import argparse
import csv
import json
import math

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "terrain_data.csv"

FEATURES = [
    "slope_deg",
    "roughness_m",
    "local_relief_m",
    "slope_std_deg",
    "flat_fraction",
]

CONDITIONS = {
    "mobility": [
        "slope_deg",
        "roughness_m",
        "local_relief_m",
        "slope_std_deg",
    ],
    "navigation": [
        "roughness_m",
        "local_relief_m",
        "slope_std_deg",
    ],
    "robotic_operations": [
        "slope_deg",
        "roughness_m",
        "flat_fraction",
    ],
}


def load_data(csv_path):
    with Path(csv_path).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        required = {"region", "body", *FEATURES}
        missing = required.difference(
            reader.fieldnames or []
        )

        if missing:
            raise ValueError(
                f"Missing columns: {sorted(missing)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("The data file is empty")

    identities = set()

    for number, row in enumerate(rows, start=2):
        for column in ("region", "body"):
            row[column] = (row[column] or "").strip()

            if not row[column]:
                raise ValueError(
                    f"Row {number}: missing {column}"
                )

        if row["body"] not in {"Earth", "Moon", "Mars"}:
            raise ValueError(
                f"Row {number}: invalid body"
            )

        identity = (row["body"], row["region"])

        if identity in identities:
            raise ValueError(
                f"Duplicate region: {identity}"
            )

        identities.add(identity)

        for feature in FEATURES:
            try:
                value = float(row[feature])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Row {number}: invalid {feature}"
                ) from None

            if not math.isfinite(value) or value < 0:
                raise ValueError(
                    f"Row {number}: invalid {feature}"
                )

            if feature == "slope_deg" and value > 90:
                raise ValueError(
                    f"Row {number}: slope exceeds 90"
                )

            if feature.endswith("_fraction") and value > 1:
                raise ValueError(
                    f"Row {number}: {feature} "
                    "must be between 0 and 1"
                )

            row[feature] = value

    if not any(row["body"] == "Earth" for row in rows):
        raise ValueError("No Earth regions found")

    return rows


def get_selected_features(condition, selected_features):
    if (condition is None) == (selected_features is None):
        raise ValueError(
            "Choose condition OR selected_features"
        )

    if condition is not None:
        if condition not in CONDITIONS:
            raise ValueError("Unknown condition")

        return CONDITIONS[condition].copy()

    if isinstance(selected_features, str):
        raise ValueError(
            "selected_features must be a list"
        )

    selected = list(selected_features)

    if not selected:
        raise ValueError("Select at least one feature")

    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate selected features")

    if not set(selected).issubset(FEATURES):
        raise ValueError("Unknown selected features")

    return selected


def compare(
    csv_path=DATA_FILE,
    target_body="Moon",
    target_region="Connecting_Ridge",
    *,
    condition=None,
    selected_features=None,
):
    data = load_data(csv_path)

    selected = get_selected_features(
        condition, selected_features
    )

    if target_body not in {"Moon", "Mars"}:
        raise ValueError(
            "Target body must be Moon or Mars"
        )

    targets = [
        row for row in data
        if row["body"] == target_body
        and row["region"] == target_region
    ]

    if len(targets) != 1:
        raise ValueError(
            f"Target not found: {target_region}"
        )

    target = targets[0]

    earth_regions = [
        row for row in data
        if row["body"] == "Earth"
    ]

    minimums = {
        feature: min(row[feature] for row in data)
        for feature in FEATURES
    }

    maximums = {
        feature: max(row[feature] for row in data)
        for feature in FEATURES
    }

    candidates = []

    for earth in earth_regions:
        details = {}

        for feature in selected:
            difference = abs(
                earth[feature] - target[feature]
            )

            span = maximums[feature] - minimums[feature]

            normalized = (
                difference / span if span else 0.0
            )

            similarity = 100 * (1 - normalized)

            details[feature] = {
                "earth_value": earth[feature],
                "target_value": target[feature],
                "raw_difference": difference,
                "normalized_difference": normalized,
                "similarity_pct": similarity,
                "weight": 1 / len(selected),
            }

        overall = sum(
            item["similarity_pct"]
            for item in details.values()
        ) / len(selected)

        candidates.append({
            "region": earth["region"],
            "body": "Earth",
            "overall_similarity_score": overall,
            "feature_similarities": {
                feature: item["similarity_pct"]
                for feature, item in details.items()
            },
            "feature_details": details,
        })

    candidates.sort(
        key=lambda row: (
            -row["overall_similarity_score"],
            row["region"],
        )
    )

    return {
        "mode": "condition" if condition else "custom",
        "condition": condition,
        "selected_features": selected,
        "target": {
            "region": target["region"],
            "body": target["body"],
            "features": {
                feature: target[feature]
                for feature in FEATURES
            },
        },
        "best_match": candidates[0],
        "all_candidates": candidates,
        "reference_dataset": [
            {
                "region": row["region"],
                "body": row["body"],
                **{
                    feature: row[feature]
                    for feature in FEATURES
                },
            }
            for row in earth_regions
        ],
        "normalization": {
            "minimums": minimums,
            "maximums": maximums,
            "constant_features": [
                feature for feature in FEATURES
                if maximums[feature] == minimums[feature]
            ],
        },
    }
