import csv
import pickle
from pathlib import Path

from train_softmax_fault_type import CategoricalSelector, ProblemSelector


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "ora_aggregate_mobile.csv"
MODEL_FILE = BASE_DIR / "fault_type_softmax_model.pkl"
OUTPUT_FILE = DATA_DIR / "ora_aggregate_mobile_with_fault_type.csv"


def load_model(model_path: Path) -> dict:
    with model_path.open("rb") as f:
        return pickle.load(f)


def build_feature_rows(reader: csv.DictReader, text_feature: str, categorical_features: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    original_rows: list[dict[str, str]] = []
    feature_rows: list[dict[str, str]] = []

    for row in reader:
        original_rows.append(row)
        feature_rows.append(
            {
                text_feature: str(row.get("problem", "")).strip(),
                "brand": str(row.get("brand", "unknown_brand")).strip() or "unknown_brand",
                "age": str(row.get("product_age", "unknown_age")).strip() or "unknown_age",
            }
        )

    return original_rows, feature_rows


def predict_fault_types() -> None:
    payload = load_model(MODEL_FILE)
    feature_pipeline = payload["feature_pipeline"]
    classifier = payload["classifier"]
    text_feature = payload["text_feature"]
    categorical_features = payload["categorical_features"]

    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        if reader.fieldnames is None:
            raise ValueError(f"No CSV header found in {INPUT_FILE}.")

        original_rows, feature_rows = build_feature_rows(reader, text_feature, categorical_features)

    feature_matrix = feature_pipeline.transform(feature_rows)
    predictions = classifier.predict(feature_matrix)

    output_fieldnames = list(reader.fieldnames) + ["fault_type"]
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=output_fieldnames)
        writer.writeheader()

        for row, prediction in zip(original_rows, predictions, strict=True):
            output_row = dict(row)
            output_row["fault_type"] = str(prediction)
            writer.writerow(output_row)

    print(f"Wrote {len(original_rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    predict_fault_types()
