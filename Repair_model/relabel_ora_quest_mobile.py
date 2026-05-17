from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "ora_quest_mobile.csv"
OUTPUT_FILE = BASE_DIR / "data" / "ora_quest_mobile_brand_fault_type.csv"


APPLE_LABELS = [
    "Battery",
    "Back glass damage",
    "Rear camera damage",
    "Screen damage",
    "Screen and back glass damage",
    "Other damage",
]

SAMSUNG_LABELS = [
    "Backglass cracked",
    "Battery issues",
    "Charge port issue",
    "Display issues",
    "Front camera Issues",
    "Rear Camera Issues",
    "Other damage",
]


def normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def map_apple(original_fault_type: str, problem: str) -> str:
    text = f"{original_fault_type} {problem}".lower()

    if has_any(text, ["screen", "display", "touch", "glass crack", "cracked screen"]):
        if has_any(text, ["back glass", "backglass", "back cover"]):
            return "Screen and back glass damage"
        return "Screen damage"

    if has_any(text, ["back glass", "backglass", "back cover"]):
        return "Back glass damage"

    if has_any(text, ["battery", "power", "no power", "won't charge", "wont charge"]):
        return "Battery"

    if has_any(text, ["camera", "lens", "rear cam", "rear camera"]):
        return "Rear camera damage"

    return "Other damage"


def map_samsung(original_fault_type: str, problem: str) -> str:
    text = f"{original_fault_type} {problem}".lower()

    if has_any(text, ["back glass", "backglass", "back cover"]):
        return "Backglass cracked"

    if has_any(text, ["battery", "power", "no power", "won't charge", "wont charge"]):
        return "Battery issues"

    if has_any(text, ["charge port", "charging port", "usb", "port"]):
        return "Charge port issue"

    if has_any(text, ["front camera", "selfie camera"]):
        return "Front camera Issues"

    if has_any(text, ["rear camera", "camera", "lens"]):
        return "Rear Camera Issues"

    if has_any(text, ["screen", "display", "touch", "glass crack", "cracked screen"]):
        return "Display issues"

    return "Other damage"


def map_fault_type(brand: str, original_fault_type: str, problem: str) -> str:
    brand_lower = normalize_text(brand)
    if brand_lower == "apple":
        return map_apple(original_fault_type, problem)
    if brand_lower == "samsung":
        return map_samsung(original_fault_type, problem)
    return original_fault_type.strip() or "Other damage"


def main() -> None:
    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f_in, OUTPUT_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as f_out:
        reader = csv.DictReader(f_in)
        if reader.fieldnames is None:
            raise ValueError(f"No CSV header found in {INPUT_FILE}.")

        fieldnames = ["original_fault_type", "brand", "age", "problem", "fault_type"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        rows = 0
        brand_counts = {"apple": 0, "samsung": 0, "other": 0}
        label_counts: dict[str, int] = {}

        for row in reader:
            brand = str(row.get("brand", "")).strip()
            original_fault_type = str(row.get("fault_type", "")).strip()
            problem = str(row.get("problem", "")).strip()
            age = str(row.get("age", "")).strip()

            new_fault_type = map_fault_type(brand, original_fault_type, problem)
            writer.writerow(
                {
                    "original_fault_type": original_fault_type,
                    "brand": brand,
                    "age": age,
                    "problem": problem,
                    "fault_type": new_fault_type,
                }
            )

            rows += 1
            brand_key = normalize_text(brand) or "other"
            brand_counts[brand_key] = brand_counts.get(brand_key, 0) + 1
            label_counts[new_fault_type] = label_counts.get(new_fault_type, 0) + 1

    print(f"Wrote {rows} rows to {OUTPUT_FILE}")
    print(f"Brand counts: {brand_counts}")
    print("New fault_type counts:")
    for label, count in sorted(label_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
