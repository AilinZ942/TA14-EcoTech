from __future__ import annotations

import csv
import json
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Any

import requests
from flask import Blueprint, jsonify, request

from routes.login import login_required
import repair_status_transformers  # noqa: F401

repair_check_bp = Blueprint("repair_check", __name__)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = BACKEND_ROOT / "db"
USED_PRICE_FILE = DB_DIR / "apple_used_price.csv"
REPAIR_PRICE_FILE = DB_DIR / "apple_repair_price.csv"
REPAIR_STATUS_MODEL_FILE = BACKEND_ROOT / "repair_status_softmax_model.pkl"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

VALID_BRANDS = {"apple": "Apple"}

MODEL_STATE: dict[str, Any] = {"payload": None, "load_error": None}
USED_PRICE_LOOKUP: dict[tuple[str, str, str], float] = {}
REPAIR_PRICE_LOOKUP: dict[tuple[str, str, str], float] = {}


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def build_lookup_key(*parts: str) -> tuple[str, ...]:
    return tuple(normalize_key(part) for part in parts)


def load_used_price_table() -> None:
    global USED_PRICE_LOOKUP

    lookup: dict[tuple[str, str, str], float] = {}

    with USED_PRICE_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            brand = str(row["brand"]).strip()
            model = str(row["model"]).strip()
            storage = str(row["storage"]).strip()
            price_raw = str(row["price_aud"]).strip()
            if not brand or not model or not storage or not price_raw:
                continue

            try:
                price = float(price_raw)
            except ValueError:
                continue

            lookup[build_lookup_key(brand, model, storage)] = price

    USED_PRICE_LOOKUP = lookup


def load_repair_price_table() -> None:
    global REPAIR_PRICE_LOOKUP

    lookup: dict[tuple[str, str, str], float] = {}
    with REPAIR_PRICE_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) < 3:
            raise ValueError("Repair price CSV does not contain usable headers.")

        fault_columns = [column for column in reader.fieldnames[2:] if column and column.strip()]
        for row in reader:
            brand = str(row[reader.fieldnames[0]]).strip()
            model = str(row[reader.fieldnames[1]]).strip()
            if not brand or not model:
                continue
            for fault_type in fault_columns:
                value = str(row.get(fault_type, "")).strip()
                if not value:
                    continue
                try:
                    price = float(value)
                except ValueError:
                    continue
                lookup[build_lookup_key(brand, model, fault_type)] = price

    REPAIR_PRICE_LOOKUP = lookup


def load_repair_status_model() -> None:
    try:
        with REPAIR_STATUS_MODEL_FILE.open("rb") as f:
            MODEL_STATE["payload"] = pickle.load(f)
            MODEL_STATE["load_error"] = None
    except Exception as exc:  # pragma: no cover - startup fallback
        MODEL_STATE["payload"] = None
        MODEL_STATE["load_error"] = str(exc)
        logging.exception("failed to load repair status model")


def ensure_tables_loaded() -> None:
    if not USED_PRICE_LOOKUP:
        load_used_price_table()
    if not REPAIR_PRICE_LOOKUP:
        load_repair_price_table()
    if MODEL_STATE["payload"] is None and MODEL_STATE["load_error"] is None:
        load_repair_status_model()


def lookup_used_price(brand: str, model: str, storage: str) -> float | None:
    return USED_PRICE_LOOKUP.get(build_lookup_key(brand, model, storage))


def lookup_repair_price(brand: str, model: str, fault_type: str) -> float | None:
    return REPAIR_PRICE_LOOKUP.get(build_lookup_key(brand, model, fault_type))


def classify_repair_status(brand: str, age: str, problem: str, fault_type: str) -> tuple[str | None, dict[str, float]]:
    payload = MODEL_STATE["payload"]
    if not payload:
        raise RuntimeError("Repair status model is not available.")

    feature_pipeline = payload["feature_pipeline"]
    classifier = payload["classifier"]
    class_names = payload.get("class_names") or []

    feature_rows = [
        {
            "brand": brand,
            "age": age,
            "fault_type": fault_type,
            "problem": problem,
        }
    ]
    matrix = feature_pipeline.transform(feature_rows)
    prediction = str(classifier.predict(matrix)[0])

    probabilities: dict[str, float] = {}
    if hasattr(classifier, "predict_proba"):
        proba = classifier.predict_proba(matrix)[0]
        probabilities = {
            str(class_names[index]): float(score)
            for index, score in enumerate(proba)
            if index < len(class_names)
        }

    return prediction, probabilities


def derive_recommendation(
    repair_status: str | None,
    current_price: float | None,
    repair_price: float | None,
) -> tuple[str, str, str]:
    if current_price is None or repair_price is None:
        return (
            "uncertain",
            "The pricing table could not return a complete value for this combination, so the safest move is to review the repair manually.",
            "medium",
        )

    ratio = repair_price / current_price if current_price else 1.0

    if repair_status == "End of life":
        return (
            "replace",
            "The classifier marked this device as End of life, which usually means the historical repair outcome is poor. In that case, replacement is the safer recommendation unless there is a strong reason to keep the device.",
            "high",
        )

    if ratio >= 0.6:
        return (
            "replace",
            f"The estimated repair cost is about {ratio:.0%} of the current device value, which is usually too close to replacement territory. Even if the device can be repaired, the economic upside is limited.",
            "high",
        )

    if repair_status == "Repairable" and ratio <= 0.3:
        return (
            "repair",
            "The device is classified as Repairable and the repair cost is well below the current value. That makes repair the more cost-effective choice in most cases.",
            "high",
        )

    if repair_status == "Unknown":
        return (
            "uncertain",
            "The classifier is uncertain, so the decision should lean on the repair cost versus current value. With limited confidence from the model, a manual review is safer.",
            "medium",
        )

    if ratio <= 0.45:
        return (
            "repair",
            "The repair cost is still meaningfully below the device value, so repair remains reasonable. The final choice depends on how much you want to keep using this model long term.",
            "medium",
        )

    return (
        "replace",
        "The repair cost is getting close to the device value, so replacement offers better value for money. Repair may still work technically, but it is less attractive financially.",
        "medium",
    )


SYSTEM_GUIDE = """You are EcoTech Repair Decision Assistant.
You must follow the recommendation provided in the prompt.
Do not change the recommendation.
Rewrite the reasoning into 2 or 3 short, plain-English sentences.
Do not mention hidden chain of thought.
Be concise, practical, and friendly.
Return valid JSON with keys:
recommendation
reason
confidence
"""


def generate_ai_reason(prompt: str) -> dict[str, str]:
    if not GROQ_API_KEY:
        return {}

    try:
        response = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_GUIDE},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 260,
            },
            timeout=60,
        )
        response.raise_for_status()
        completion = response.json()
        choices = completion.get("choices") or []
        if not choices:
            return {}
        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            return {}
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return {}
        return {
            "recommendation": str(parsed.get("recommendation") or "").strip(),
            "reason": str(parsed.get("reason") or "").strip(),
            "confidence": str(parsed.get("confidence") or "").strip(),
        }
    except Exception:
        logging.exception("groq analysis failed")
        return {}


def build_ai_prompt(
    brand: str,
    model: str,
    storage: str,
    age: str,
    fault_type: str,
    problem: str,
    repair_status: str | None,
    current_price: float | None,
    repair_price: float | None,
    recommendation: str,
    reason: str,
    confidence: str,
) -> str:
    return f"""Device brand: {brand}
Device model: {model}
Storage: {storage}
Age: {age}
Fault type: {fault_type}
Problem: {problem}
Predicted repair status: {repair_status or "Unavailable"}
Current device value: {current_price if current_price is not None else "Unavailable"}
Estimated repair cost: {repair_price if repair_price is not None else "Unavailable"}

Decision from rules:
recommendation: {recommendation}
reason: {reason}
confidence: {confidence}

Rewrite the reasoning into 2 or 3 short sentences.
Keep the recommendation the same.
Return JSON only.
"""


@repair_check_bp.route("/ai/repair-decision", methods=["POST"])
@login_required
def analyze_repair_decision():
    ensure_tables_loaded()

    payload = request.get_json(silent=True) or {}
    brand = str(payload["brand"]).strip()
    model = str(payload["model"]).strip()
    storage = str(payload["storage"]).strip()
    age = str(payload["age"]).strip()
    fault_type = str(payload["fault_type"]).strip()
    problem = str(payload["problem"]).strip()

    if not brand or not model or not storage or not age or not fault_type or not problem:
        return jsonify({"detail": "Please fill in all fields before analyzing."}), 400

    canonical_brand = VALID_BRANDS.get(normalize_key(brand))
    if not canonical_brand:
        return jsonify({"detail": "Only Apple is available for now."}), 400

    if not MODEL_STATE["payload"]:
        return (
            jsonify(
                {
                    "detail": "Repair status model is not available. Please check the backend environment.",
                    "model_error": MODEL_STATE["load_error"] or "model-not-loaded",
                }
            ),
            503,
        )

    current_price = lookup_used_price(canonical_brand, model, storage)
    repair_price = lookup_repair_price(canonical_brand, model, fault_type)
    repair_status, probabilities = classify_repair_status(canonical_brand, age, problem, fault_type)

    recommendation, reason, confidence = derive_recommendation(repair_status, current_price, repair_price)

    ai_prompt = build_ai_prompt(
        brand=canonical_brand,
        model=model,
        storage=storage,
        age=age,
        fault_type=fault_type,
        problem=problem,
        repair_status=repair_status,
        current_price=current_price,
        repair_price=repair_price,
        recommendation=recommendation,
        reason=reason,
        confidence=confidence,
    )
    ai_result = generate_ai_reason(ai_prompt)

    final_recommendation = ai_result.get("recommendation") or recommendation
    final_reason = ai_result.get("reason") or reason
    final_confidence = ai_result.get("confidence") or confidence

    return jsonify(
        {
            "brand": canonical_brand,
            "model": model,
            "storage": storage,
            "age": age,
            "fault_type": fault_type,
            "problem": problem,
            "current_price_aud": current_price,
            "repair_price_aud": repair_price,
            "repair_status": repair_status,
            "repair_status_probabilities": probabilities,
            "recommendation": final_recommendation,
            "reason": final_reason,
            "confidence": final_confidence,
            "decision_source": "rules + ai-summary" if ai_result else "rules",
            "groq_model": GROQ_MODEL if GROQ_API_KEY else None,
        }
    )


try:
    load_used_price_table()
    load_repair_price_table()
    load_repair_status_model()
except Exception:
    logging.exception("repair decision tables failed to load at import time")
