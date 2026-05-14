from __future__ import annotations

import os
import re
import logging
from typing import Literal

from flask import Blueprint, jsonify, request
import requests

from routes.login import login_required

optimizer_bp = Blueprint("optimizer", __name__)

DeviceType = Literal["laptop", "phone"]
IssueCategory = Literal["slow_performance", "battery_drain", "storage_full", "general"]

DEVICE_TYPES: dict[DeviceType, dict[str, str]] = {
    "laptop": {
        "label": "Laptop",
        "summary": "Best for study, work, and longer sessions at a desk.",
    },
    "phone": {
        "label": "Phone",
        "summary": "Best for everyday mobile use and quick checks on the go.",
    },
}

ISSUE_LABELS: dict[IssueCategory, str] = {
    "slow_performance": "Slow performance",
    "battery_drain": "Battery drain",
    "storage_full": "Storage full",
    "general": "General device care",
}

ISSUE_EXPLANATIONS: dict[IssueCategory, str] = {
    "slow_performance": (
        "Your device may be running slowly because too many apps are open, the storage is nearly full, "
        "or the device is working harder than usual."
    ),
    "battery_drain": (
        "Your battery may drain quickly because the screen is too bright, apps are using too much power, "
        "or the battery is getting older."
    ),
    "storage_full": (
        "Your device has less room for updates, apps, and temporary files when storage is nearly full, "
        "which can also make it feel slower."
    ),
    "general": (
        "Your issue looks like a general device care question. A good first step is to check storage, "
        "battery health, software updates, and background apps."
    ),
}

SLOW_KEYWORDS = [
    "slow",
    "lag",
    "freez",
    "stuck",
    "unresponsive",
    "performance",
    "crash",
]

BATTERY_KEYWORDS = [
    "battery",
    "drain",
    "charge",
    "charging",
    "power",
    "overheat",
    "hot",
]

STORAGE_KEYWORDS = [
    "storage",
    "space",
    "full",
    "memory",
    "delete",
    "files",
    "photos",
    "videos",
]

SYSTEM_GUIDE = """You are EcoTech AI Device Optimizer.
Explain device issues in simple, non-technical English.
Focus only on laptops and phones.
Do not mention dangerous repairs, opening batteries, or data loss risks.
Return exactly this structure:
WHAT MAY BE AFFECTING YOUR DEVICE: one short paragraph describing only the likely causes or factors
TIPS:
- tip 1
- tip 2
- tip 3
- tip 4
Do not put any advice, fixes, or action steps inside the explanation section.
Keep the answer friendly, practical, and concise.
"""

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
LLAMA_TEMPERATURE = float(os.environ.get("LLAMA_TEMPERATURE", "0.2"))
LLAMA_TOP_P = float(os.environ.get("LLAMA_TOP_P", "0.9"))
LLAMA_MAX_TOKENS = int(os.environ.get("LLAMA_MAX_TOKENS", "260"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def classify_issue(issue_text: str) -> IssueCategory:
    normalized = normalize_text(issue_text)

    if any(keyword in normalized for keyword in BATTERY_KEYWORDS):
        return "battery_drain"
    if any(keyword in normalized for keyword in STORAGE_KEYWORDS):
        return "storage_full"
    if any(keyword in normalized for keyword in SLOW_KEYWORDS):
        return "slow_performance"
    return "general"


def clean_device_type(device_type: str | None) -> DeviceType:
    normalized = normalize_text(device_type or "")
    if normalized not in DEVICE_TYPES:
        raise ValueError("Please choose a valid device type.")
    return normalized


def build_prompt(device_type: DeviceType, issue_text: str) -> str:
    device_label = DEVICE_TYPES[device_type]["label"]
    issue_category = classify_issue(issue_text)
    issue_hints = {
        "slow_performance": "Likely causes: background apps, storage pressure, software bugs, overheating, or heavy app usage.",
        "battery_drain": "Likely causes: screen brightness, background activity, battery age, charging habits, or location services.",
        "storage_full": "Likely causes: large files, photos and videos, downloads, app data, or too many unused apps.",
        "general": "Likely causes: app usage, battery age, storage pressure, software updates, or device wear.",
    }

    return f"""Device type: {device_label}
Issue hint: {issue_category}
{issue_hints[issue_category]}
User issue:
{issue_text.strip()}

Write a practical answer in simple English.
Do not be vague.
Focus on the selected device type.
Return exactly this structure:
WHAT MAY BE AFFECTING YOUR DEVICE: one short paragraph describing only the likely causes or factors
TIPS:
- tip 1
- tip 2
- tip 3
- tip 4
Do not include any fixes or actions in the first paragraph.
"""


def parse_model_text(text: str) -> tuple[str, list[str]]:
    cleaned = text.strip()
    explanation = ""
    tips: list[str] = []

    explanation_match = re.search(
        r"(?:WHAT MAY BE AFFECTING YOUR DEVICE|EXPLANATION):\s*(.*?)(?:\nTIPS:|\Z)",
        cleaned,
        flags=re.S | re.I,
    )
    if explanation_match:
        explanation = explanation_match.group(1).strip()
    else:
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            explanation = lines[0]

    tips_block = ""
    tips_match = re.search(r"TIPS:\s*(.*)", cleaned, flags=re.S | re.I)
    if tips_match:
        tips_block = tips_match.group(1).strip()
    else:
        tips_block = cleaned

    for line in tips_block.splitlines():
        item = re.sub(r"^[-*•]\s*", "", line.strip())
        if item and item.upper() not in {"EXPLANATION:", "WHAT MAY BE AFFECTING YOUR DEVICE:", "TIPS:"}:
            tips.append(item)

    if not explanation:
        explanation = "This issue usually improves when you remove pressure from the device and make a few simple changes."

    explanation = re.sub(
        r"\b(you can|you should|try to|restart|close|delete|turn off|update|clean up|free up|install)\b.*",
        "",
        explanation,
        flags=re.I,
    ).strip()
    if not explanation:
        explanation = "This issue is often caused by a few common device factors."

    deduped: list[str] = []
    for item in tips:
        if item not in deduped:
            deduped.append(item)

    return explanation, deduped[:4]


def generate_reply(prompt: str) -> tuple[str, str]:
    try:
        if not GROQ_API_KEY:
            return "", "groq-missing-api-key"

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
                "temperature": LLAMA_TEMPERATURE,
                "top_p": LLAMA_TOP_P,
                "max_tokens": LLAMA_MAX_TOKENS,
            },
            timeout=60,
        )
        response.raise_for_status()

        completion = response.json()
        choices = completion.get("choices") or []
        if not choices:
            return "", GROQ_MODEL

        message = choices[0].get("message") or {}
        text = str(message.get("content") or "").strip()
        return text, GROQ_MODEL
    except Exception:
        logging.exception("groq generation failed")
        return "", "groq-generation-failed"


@optimizer_bp.route("/ai/device-optimizer", methods=["POST"])
@login_required
def optimize_device():
    payload = request.get_json(silent=True) or {}
    try:
        device_type = clean_device_type(payload.get("device_type"))
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400

    issue_text = str(payload.get("issue_text") or "").strip()
    if not issue_text:
        return jsonify({"detail": "Please describe the issue before getting optimisation tips."}), 400

    issue_category = classify_issue(issue_text)
    prompt = build_prompt(device_type=device_type, issue_text=issue_text)
    generated_text, model_name = generate_reply(prompt)

    if not generated_text:
        return (
            jsonify(
                {
                    "detail": "The Groq model is not available or did not return a response. Please check the API key and Groq setup.",
                    "model": model_name,
                }
            ),
            503,
        )

    issue_explanation, suggestions = parse_model_text(generated_text)

    return jsonify(
        {
            "device_type": device_type,
            "device_label": DEVICE_TYPES[device_type]["label"],
            "device_summary": DEVICE_TYPES[device_type]["summary"],
            "issue_category": issue_category,
            "issue_label": ISSUE_LABELS[issue_category],
            "issue_explanation": issue_explanation,
            "suggestions": suggestions,
            "model": model_name,
        }
    )
