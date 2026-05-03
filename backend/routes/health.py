"""Health-data endpoints.

This module now contains the merged health routes that used to be split
between `health.py` and `health_routes.py`.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from services import health_service
from utils.helpers import fail, ok


health_bp = Blueprint("health", __name__)


HEALTH_DATA = {
    "summaryCards": [
        {
            "value": "40",
            "label": "State-year pairs",
            "text": "State-year comparisons were used to connect pollution indicators with health outcomes.",
        },
        {
            "value": "12",
            "label": "Health metrics",
            "text": "The analysis covers mortality, premature death, avoidable death, and rate-based outcomes.",
        },
        {
            "value": "27",
            "label": "Emission predictors",
            "text": "Air, land, and water emission indicators were compared with health outcomes.",
        },
        {
            "value": "0.94",
            "label": "Strongest signal",
            "text": "Potential years of life lost showed the strongest Spearman signal with total water emissions.",
        },
    ],
    "pathwayChains": [
        {
            "title": "E-waste to environment",
            "tag": "Chain 1",
            "steps": [
                "E-waste generation",
                "Hazardous disposal and recycling pressure",
                "Air, land, and water emissions",
            ],
            "evidence": "The environmental analysis links e-waste pressure with pollutant release patterns, especially heavy metal and total emission indicators.",
        },
        {
            "title": "Environment to health",
            "tag": "Chain 2",
            "steps": [
                "Pollution indicators",
                "State-year health comparison",
                "Mortality and burden signals",
            ],
            "evidence": "The health analysis compares emission indicators with outcomes such as deaths, premature deaths, avoidable deaths, and years of life lost.",
        },
    ],
    "environmentSummary": [
        {
            "metric": "Hazardous recycling tonnes",
            "pollutant": "PM2.5 air",
            "corr": 0.88,
            "context": "Strongest overall environment signal across 8 states.",
        },
        {
            "metric": "E-waste proxy tonnes",
            "pollutant": "Copper land",
            "corr": 0.84,
            "context": "E-waste pressure aligns with land-based copper emission burden.",
        },
        {
            "metric": "Hazardous disposal tonnes",
            "pollutant": "Copper land",
            "corr": 0.82,
            "context": "Disposal pressure shows a similar pollutant relationship.",
        },
    ],
    "stateEnvironmentSignals": [
        {"state": "WA", "pollutant": "Mercury air", "corr": -0.91},
        {"state": "NT", "pollutant": "TVOC air", "corr": 0.85},
        {"state": "VIC", "pollutant": "Total air emission", "corr": -0.82},
        {"state": "NSW", "pollutant": "TVOC air", "corr": -0.8},
        {"state": "TAS", "pollutant": "Zinc land", "corr": 0.73},
    ],
    "topEwasteStates": [
        {"state": "NSW", "ewaste": "151.4M", "air": "12.7B kg", "water": "596.9M kg"},
        {"state": "QLD", "ewaste": "150.9M", "air": "18.0B kg", "water": "60.4M kg"},
        {"state": "VIC", "ewaste": "110.8M", "air": "5.9B kg", "water": "156.4M kg"},
        {"state": "WA", "ewaste": "54.7M", "air": "13.3B kg", "water": "118.0M kg"},
        {"state": "SA", "ewaste": "38.0M", "air": "3.7B kg", "water": "50.9M kg"},
    ],
    "findings": [
        {
            "metric": "Potential Years of Life Lost",
            "signal": "Total Water Emission",
            "spearman": 0.94,
            "pearson": 0.76,
        },
        {
            "metric": "Potentially Avoidable Deaths",
            "signal": "Total Water Emission",
            "spearman": 0.93,
            "pearson": 0.76,
        },
        {
            "metric": "Premature Deaths",
            "signal": "Total Water Emission",
            "spearman": 0.93,
            "pearson": 0.78,
        },
        {
            "metric": "Deaths",
            "signal": "Total Water Emission",
            "spearman": 0.9,
            "pearson": 0.8,
        },
        {
            "metric": "Crude Rate",
            "signal": "Zinc Water",
            "spearman": 0.82,
            "pearson": 0.8,
        },
    ],
    "modelCards": [
        {
            "title": "Deaths",
            "r2": "0.99",
            "adjusted": "0.98",
            "note": "Mortality outcomes show a strong packaged statistical fit in the prepared model summary.",
        },
        {
            "title": "Premature Deaths",
            "r2": "1.00",
            "adjusted": "0.98",
            "note": "Water-emission signals repeatedly appear in mortality-related outcome rankings.",
        },
        {
            "title": "Crude Rate",
            "r2": "0.98",
            "adjusted": "0.94",
            "note": "Zinc water emissions are the strongest fixed correlation signal for crude health rate.",
        },
    ],
}


@health_bp.route("/health/all", methods=["GET"])
def get_health_all():
    return jsonify(HEALTH_DATA)


# NOTE:
# The database-backed health routes are intentionally disabled for now because
# the corresponding datasets have not been deployed to the cloud database yet.
# Re-enable these routes once the backend data is available again.
#
@health_bp.route("/health/all_2", methods=["GET"])
def get_all():
    try:
        data = health_service.list_all(
            year=request.args.get("year"),
            sex=request.args.get("sex"),
            cancer_type=request.args.get("cancer_type"),
        )
        return ok(data, meta={"count": len(data), "source": "postgresql"})
    except Exception as e:
        return fail(f"Database error: {e}", 503)


@health_bp.route("/health/filters", methods=["GET"])
def get_filters():
    try:
        data = health_service.list_filter_options()
        return ok(data)
    except Exception as e:
        return fail(f"Database error: {e}", 503)
