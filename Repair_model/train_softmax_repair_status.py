import csv
import pickle
import random
import sys
from pathlib import Path
from typing import Any, TypeAlias

from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from repair_status_transformers import CategoricalSelector, ProblemSelector  # noqa: E402


DATA_FILE = BASE_DIR / "data" / "ora_aggregate_mobile_with_fault_type.csv"
MODEL_FILE = BASE_DIR / "repair_status_softmax_model.pkl"
PLOT_FILE = BASE_DIR / "repair_status_softmax_training.png"
LABEL_COLUMN = "repair_status"
TEXT_FEATURE = "problem"
CATEGORICAL_FEATURES = ["brand", "age", "fault_type"]
EPOCHS = 30
TEST_RATIO = 0.2
SEED = 42

FeatureRow: TypeAlias = dict[str, str]
TrainingHistoryItem: TypeAlias = dict[str, float]
SerializedModel: TypeAlias = dict[str, Any]


def normalize_label(label: str) -> str:
    normalized = label.strip()
    lowered = normalized.lower()
    if lowered in {"fixed", "repairable"}:
        return "Repairable"
    if lowered == "end of life":
        return "End of life"
    if lowered == "unknown":
        return "Unknown"
    return normalized


def load_rows(csv_path: Path) -> tuple[list[FeatureRow], list[str]]:
    rows = []
    labels = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = normalize_label(str(row[LABEL_COLUMN]).strip())
            problem = str(row[TEXT_FEATURE]).strip()
            if not label or not problem:
                continue

            rows.append(
                {
                    TEXT_FEATURE: problem,
                    "brand": str(row["brand"]).strip(),
                    "age": str(row["age"]).strip(),
                    "fault_type": str(row["fault_type"]).strip(),
                }
            )
            labels.append(label)

    return rows, labels


def build_feature_pipeline() -> FeatureUnion:
    return FeatureUnion(
        transformer_list=[
            (
                "problem_tfidf",
                Pipeline(
                    steps=[
                        ("select_problem", ProblemSelector()),
                        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2)),
                    ]
                ),
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("select_categorical", CategoricalSelector()),
                        ("dictvec", DictVectorizer()),
                    ]
                ),
            ),
        ]
    )


def build_classifier(random_state: int) -> SGDClassifier:
    return SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=0.0001,
        learning_rate="optimal",
        random_state=random_state,
    )


def save_model(
    model_path: Path,
    feature_pipeline: FeatureUnion,
    classifier: SGDClassifier,
    class_names: list[str],
) -> None:
    payload: SerializedModel = {
        "feature_pipeline": feature_pipeline,
        "classifier": classifier,
        "class_names": class_names,
        "text_feature": TEXT_FEATURE,
        "categorical_features": CATEGORICAL_FEATURES,
    }
    with model_path.open("wb") as f:
        pickle.dump(payload, f)


def save_plot(history: list[TrainingHistoryItem], plot_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    epochs = [item["epoch"] for item in history]
    train_loss = [item["train_loss"] for item in history]
    val_loss = [item["val_loss"] for item in history]
    train_acc = [item["train_accuracy"] for item in history]
    val_acc = [item["val_accuracy"] for item in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].plot(epochs, train_loss, label="Train Loss", linewidth=2)
    axes[0].plot(epochs, val_loss, label="Validation Loss", linewidth=2)
    axes[0].set_title("Cross-Entropy Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, train_acc, label="Train Accuracy", linewidth=2)
    axes[1].plot(epochs, val_acc, label="Validation Accuracy", linewidth=2)
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)
    return True


def train_and_track(
    rows: list[FeatureRow],
    labels: list[str],
    epochs: int,
    test_ratio: float,
    seed: int,
) -> tuple[SGDClassifier, FeatureUnion, list[str], list[TrainingHistoryItem], int, int, int]:
    x_train, x_val, y_train, y_val = train_test_split(
        rows,
        labels,
        test_size=test_ratio,
        random_state=seed,
        stratify=labels,
    )

    feature_pipeline = build_feature_pipeline()
    x_train_matrix = feature_pipeline.fit_transform(x_train)
    x_val_matrix = feature_pipeline.transform(x_val)

    class_names = sorted(set(y_train))
    classifier = build_classifier(random_state=seed)
    history = []
    rng = random.Random(seed)
    indices = list(range(len(y_train)))

    for epoch in range(1, epochs + 1):
        rng.shuffle(indices)
        shuffled_x = x_train_matrix[indices]
        shuffled_y = [y_train[i] for i in indices]

        classifier.partial_fit(shuffled_x, shuffled_y, classes=class_names)

        train_probs = classifier.predict_proba(x_train_matrix)
        val_probs = classifier.predict_proba(x_val_matrix)
        train_preds = classifier.predict(x_train_matrix)
        val_preds = classifier.predict(x_val_matrix)

        train_loss = log_loss(y_train, train_probs, labels=class_names)
        val_loss = log_loss(y_val, val_probs, labels=class_names)
        train_acc = accuracy_score(y_train, train_preds)
        val_acc = accuracy_score(y_val, val_preds)

        history.append(
            {
                "epoch": epoch,
                "train_loss": float(train_loss),
                "train_accuracy": float(train_acc),
                "val_loss": float(val_loss),
                "val_accuracy": float(val_acc),
            }
        )
        print(
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )

    feature_count = x_train_matrix.shape[1]
    return classifier, feature_pipeline, class_names, history, len(y_train), len(y_val), feature_count


def main() -> None:
    rows, labels = load_rows(DATA_FILE)
    if len(rows) < 10:
        raise ValueError("Not enough rows to train.")

    classifier, feature_pipeline, class_names, history, train_count, val_count, feature_count = train_and_track(
        rows=rows,
        labels=labels,
        epochs=EPOCHS,
        test_ratio=TEST_RATIO,
        seed=SEED,
    )

    final = history[-1]
    print()
    print(f"Train rows: {train_count} | Validation rows: {val_count}")
    print(f"Classes: {len(class_names)} | Features: {feature_count}")
    print(f"Final train accuracy: {final['train_accuracy']:.4f}")
    print(f"Final validation accuracy: {final['val_accuracy']:.4f}")

    save_model(MODEL_FILE, feature_pipeline, classifier, class_names)
    print(f"Saved model to: {MODEL_FILE}")

    plot_saved = save_plot(history, PLOT_FILE)
    if plot_saved:
        print(f"Saved plot to: {PLOT_FILE}")
    else:
        print("Skipped plot: matplotlib is not available.")


if __name__ == "__main__":
    main()
