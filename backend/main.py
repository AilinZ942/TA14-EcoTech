from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2.extras
from psycopg2 import pool


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

load_dotenv()

connection_pool = None

# AI section starts here: config, classification, prompt building, model loading, route.
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

ISSUE_CATEGORIES: dict[IssueCategory, dict[str, object]] = {
    "slow_performance": {
        "label": "Slow performance",
        "explanation": (
            "Your device may be running slowly because too many apps are open, the storage is nearly full, "
            "or the device is working harder than usual."
        ),
        "suggestions": {
            "laptop": [
                "Restart the laptop to clear temporary clutter.",
                "Close apps you are not using and keep only the important ones open.",
                "Remove large files or move them to cloud storage or an external drive.",
                "Check for software updates so the system can run more smoothly.",
            ],
            "phone": [
                "Close apps running in the background and restart the phone.",
                "Delete unused apps, photos, or videos that you no longer need.",
                "Turn off battery-heavy features you are not using, like constant location tracking.",
                "Update the phone software so it can stay stable and secure.",
            ],
        },
    },
    "battery_drain": {
        "label": "Battery drain",
        "explanation": (
            "Your battery may drain quickly because the screen is too bright, apps are using too much power, "
            "or the battery is getting older."
        ),
        "suggestions": {
            "laptop": [
                "Lower screen brightness and turn on power saving mode.",
                "Check which apps use the most power and close the ones you do not need.",
                "Keep the laptop cool because heat can make battery life worse.",
                "If the battery is old, consider a battery replacement instead of replacing the whole laptop.",
            ],
            "phone": [
                "Lower screen brightness and shorten the screen timeout.",
                "Close battery-hungry apps and switch off features you do not need.",
                "Avoid leaving the phone in hot places like a car or direct sun.",
                "If the battery is aging, a replacement battery may be better than a new phone.",
            ],
        },
    },
    "storage_full": {
        "label": "Storage full",
        "explanation": (
            "Your device has less room for updates, apps, and temporary files when storage is nearly full, "
            "which can also make it feel slower."
        ),
        "suggestions": {
            "laptop": [
                "Delete files you no longer need, especially large downloads and duplicate copies.",
                "Move photos, videos, and documents to cloud storage or an external drive.",
                "Empty the recycle bin or trash so deleted files are fully removed.",
                "Uninstall apps you do not use anymore.",
            ],
            "phone": [
                "Delete old photos, videos, and downloads you do not need anymore.",
                "Clear apps or chats that store a lot of media and take up space.",
                "Use cloud backup for photos so you can free up local storage.",
                "Remove apps you rarely use to create more space and keep updates working.",
            ],
        },
    },
    "general": {
        "label": "General device care",
        "explanation": (
            "Your issue looks like a general device care question. A good first step is to check storage, "
            "battery health, software updates, and background apps."
        ),
        "suggestions": {
            "laptop": [
                "Restart the laptop if it has been on for a long time.",
                "Install software updates when they are available.",
                "Close unused apps and browser tabs to reduce pressure on the system.",
                "Back up important files so you can clean up old storage safely.",
            ],
            "phone": [
                "Restart the phone if it has been running for a long time.",
                "Install phone software updates when they are available.",
                "Close unused apps and review which apps use the most battery.",
                "Back up important photos and files so you can free up space safely.",
            ],
        },
    },
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
EXPLANATION: one short paragraph
TIPS:
- tip 1
- tip 2
- tip 3
- tip 4
Keep the answer friendly, practical, and concise.
"""

# 1) Input cleanup and issue classification
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


def get_suggestions(device_type: DeviceType, issue_category: IssueCategory) -> list[str]:
    suggestions_by_device = ISSUE_CATEGORIES[issue_category]["suggestions"]
    return list(suggestions_by_device[device_type])


def build_prompt(device_type: DeviceType, issue_text: str) -> str:
    device_label = DEVICE_TYPES[device_type]["label"]
    issue_category = classify_issue(issue_text)
    issue_hints = {
        "slow_performance": "Common focus areas: background apps, storage pressure, software updates, restart, overheating.",
        "battery_drain": "Common focus areas: screen brightness, background activity, battery health, charging habits, location services.",
        "storage_full": "Common focus areas: large files, photos and videos, downloads, app data, cloud backup, uninstalling unused apps.",
        "general": "Common focus areas: updates, background apps, battery health, storage, and basic device maintenance.",
    }

    return f"""Device type: {device_label}
Issue hint: {issue_category}
{issue_hints[issue_category]}
User issue:
{issue_text.strip()}

Write a practical answer in simple English.
Do not be vague.
Give specific actions the user can do right now.
Focus on the selected device type.
Return exactly this structure:
EXPLANATION: one short paragraph
TIPS:
- tip 1
- tip 2
- tip 3
- tip 4
"""


# 2) Parse the model output into explanation + bullet tips
def parse_model_text(text: str) -> tuple[str, list[str]]:
    cleaned = text.strip()
    explanation = ""
    tips: list[str] = []

    explanation_match = re.search(r"EXPLANATION:\s*(.*?)(?:\nTIPS:|\Z)", cleaned, flags=re.S | re.I)
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
        if item and item.upper() not in {"EXPLANATION:", "TIPS:"}:
            tips.append(item)

    if not explanation:
        explanation = "This issue usually improves when you remove pressure from the device and make a few simple changes."

    deduped: list[str] = []
    for item in tips:
        if item not in deduped:
            deduped.append(item)

    return explanation, deduped[:4]


# 3) Load the Qwen GGUF model through llama-cpp-python or fall back if the environment cannot support it
QWEN_MODEL_REPO_ID = os.environ.get("QWEN_MODEL_REPO_ID", "Qwen/Qwen2.5-3B-Instruct-GGUF")
QWEN_MODEL_FILENAME = os.environ.get("QWEN_MODEL_FILENAME", "*q4_k_m.gguf")
LLAMA_N_CTX = int(os.environ.get("LLAMA_N_CTX", "2048"))
LLAMA_N_THREADS = int(os.environ.get("LLAMA_N_THREADS", "2"))
LLAMA_N_BATCH = int(os.environ.get("LLAMA_N_BATCH", "128"))
LLAMA_TEMPERATURE = float(os.environ.get("LLAMA_TEMPERATURE", "0.2"))
LLAMA_TOP_P = float(os.environ.get("LLAMA_TOP_P", "0.9"))
LLAMA_MAX_TOKENS = int(os.environ.get("LLAMA_MAX_TOKENS", "260"))


@lru_cache(maxsize=1)
def load_generator():
    try:
        from llama_cpp import Llama

        return Llama.from_pretrained(
            repo_id=QWEN_MODEL_REPO_ID,
            filename=QWEN_MODEL_FILENAME,
            n_ctx=LLAMA_N_CTX,
            n_threads=LLAMA_N_THREADS,
            n_batch=LLAMA_N_BATCH,
            verbose=False,
        )
    except Exception:
        return None


def generate_reply(prompt: str) -> tuple[str, str]:
    generator = load_generator()

    if generator is None:
        return "", "qwen-unavailable"

    try:
        completion = generator.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_GUIDE},
                {"role": "user", "content": prompt},
            ],
            temperature=LLAMA_TEMPERATURE,
            top_p=LLAMA_TOP_P,
            max_tokens=LLAMA_MAX_TOKENS,
        )
        choices = completion.get("choices") or []
        if not choices:
            return "", QWEN_MODEL_REPO_ID

        message = choices[0].get("message") or {}
        text = str(message.get("content") or "").strip()
        return text, QWEN_MODEL_REPO_ID
    except Exception:
        return "", "qwen-generation-failed"


# Rule-based fallback is intentionally kept here as a reference.
# Uncomment this block if you want the API to return fixed answers
# when the model is unavailable or the output is too weak.
#
# def build_fallback(issue_category: IssueCategory, device_type: DeviceType) -> tuple[str, list[str]]:
#     explanation = str(ISSUE_CATEGORIES[issue_category]["explanation"])
#     suggestions = get_suggestions(device_type, issue_category)
#     return explanation, suggestions


def get_connection_pool():
    global connection_pool

    if connection_pool is not None:
        return connection_pool

    try:
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "myuser"),
            password=os.environ.get("DB_PASSWORD", "yourpassword"),
            dbname=os.environ.get("DB_NAME", "mydb"),
            port=5432,
        )
    except Exception as exc:
        raise RuntimeError("Database unavailable") from exc

    return connection_pool


# 4) Database helper used by the location endpoint
def row_to_disposal_item(row):
    return {
        "facility_name": row["facility_name"],
        "address": row["address"],
        "suburb": row["suburb"],
        "postcode": row["postcode"],
        "state": row["state"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
    }


# 5) AI endpoint and location endpoint
def fetch_all_disposal_locations():
    try:
        pool_instance = get_connection_pool()
    except RuntimeError as exc:
        return jsonify({"detail": str(exc)}), 503

    conn = pool_instance.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                facility_name,
                address,
                suburb,
                postcode,
                state,
                latitude,
                longitude
            FROM ewaste_facilities
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY suburb, facility_name
            """
        )
        rows = cur.fetchall()
        cur.close()

        return jsonify(
            {
                "items": [row_to_disposal_item(row) for row in rows],
                "meta": {
                    "pipeline": "flask",
                    "source": "postgresql",
                },
            }
        )
    finally:
        pool_instance.putconn(conn)


@app.route("/api/ai/device-optimizer", methods=["POST"])
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
        return jsonify(
            {
                "detail": "The Qwen model is not available or did not return a response. Please check the model file and llama-cpp-python setup.",
                "model": model_name,
            }
        ), 503

    issue_explanation, suggestions = parse_model_text(generated_text)

    return jsonify(
        {
            "device_type": device_type,
            "device_label": DEVICE_TYPES[device_type]["label"],
            "device_summary": DEVICE_TYPES[device_type]["summary"],
            "issue_category": issue_category,
            "issue_label": ISSUE_CATEGORIES[issue_category]["label"],
            "issue_explanation": issue_explanation,
            "suggestions": suggestions,
            "model": model_name,
        }
    )


@app.route("/api/map/disposal-locations", methods=["GET"])
def search_all_disposal_locations():
    return fetch_all_disposal_locations()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
