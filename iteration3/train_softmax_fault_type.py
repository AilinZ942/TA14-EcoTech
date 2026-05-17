import argparse
import csv
import pickle
import random
from pathlib import Path
from typing import Any, TypeAlias

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "ora_quest_mobile_relabel.csv"
MODEL_FILE = BASE_DIR / "fault_type_softmax_model.pkl"
PLOT_FILE = BASE_DIR / "fault_type_softmax_training.png"
LABEL_COLUMN = "fault_type"
TEXT_FEATURE = "problem"
CATEGORICAL_FEATURES = ["brand", "age"]
RARE_LABEL_FALLBACK = "Other damage"

FeatureRow: TypeAlias = dict[str, str]
TrainingHistoryItem: TypeAlias = dict[str, float]
SerializedModel: TypeAlias = dict[str, Any]


class ProblemSelector(BaseEstimator, TransformerMixin):
    """Select the free-text problem field from each feature row."""

    def fit(self, rows: list[FeatureRow], y: Any = None) -> "ProblemSelector":
        return self

    def transform(self, rows: list[FeatureRow]) -> list[str]:
        return [row[TEXT_FEATURE] for row in rows]


class CategoricalSelector(BaseEstimator, TransformerMixin):
    """Select categorical metadata fields from each feature row."""

    def fit(self, rows: list[FeatureRow], y: Any = None) -> "CategoricalSelector":
        return self

    def transform(self, rows: list[FeatureRow]) -> list[FeatureRow]:
        return [{key: row[key] for key in CATEGORICAL_FEATURES} for row in rows]

def load_rows(csv_path: Path, drop_unknown: bool, drop_other: bool) -> tuple[list[FeatureRow], list[str]]:
    """Load cleaned CSV rows and optionally drop broad fallback labels."""
    rows = []
    labels = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = str(row.get(LABEL_COLUMN, "")).strip()
            problem = str(row.get(TEXT_FEATURE, "")).strip()
            if not label or not problem:
                continue
            if drop_unknown and label.lower() == "unknown":
                continue
            if drop_other and label.lower() == "other":
                continue

            rows.append(
                {
                    TEXT_FEATURE: problem,
                    "brand": str(row.get("brand", "unknown_brand")).strip() or "unknown_brand",
                    "age": str(row.get("age", "unknown_age")).strip() or "unknown_age",
                }
            )
            labels.append(label)

    return rows, labels


def collapse_rare_labels(
    rows: list[FeatureRow],
    labels: list[str],
    fallback_label: str = RARE_LABEL_FALLBACK,
    min_count: int = 2,
) -> tuple[list[FeatureRow], list[str]]:
    """Merge labels with too few samples into a stable fallback class."""
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    rare_labels = {label for label, count in counts.items() if count < min_count}
    if not rare_labels:
        return rows, labels

    if fallback_label not in counts:
        raise ValueError(
            f"Cannot collapse rare labels {sorted(rare_labels)} because fallback label '{fallback_label}' is missing."
        )

    merged_labels = [fallback_label if label in rare_labels else label for label in labels]
    merged_counts: dict[str, int] = {}
    for label in merged_labels:
        merged_counts[label] = merged_counts.get(label, 0) + 1

    print(f"Collapsed rare labels into '{fallback_label}': {sorted(rare_labels)}")
    print(f"Label counts after collapse: {merged_counts}")
    return rows, merged_labels

def build_feature_pipeline() -> FeatureUnion:
    """Combine text and categorical feature extraction into one pipeline."""
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
    """Create the linear softmax-style classifier trained with SGD."""
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
    """Persist the fitted feature pipeline and classifier for later inference."""
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
    """Plot train/validation CE loss and accuracy across epochs."""
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
    """Train for multiple epochs and collect loss/accuracy after each pass."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a softmax classifier with SGDClassifier and plot CE loss/accuracy.")
    parser.add_argument("--csv", type=Path, default=DATA_FILE, help="Path to ora_quest_mobile_clean.csv")
    parser.add_argument("--model-out", type=Path, default=MODEL_FILE, help="Where to save the trained model")
    parser.add_argument("--plot-out", type=Path, default=PLOT_FILE, help="Where to save the training plot")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--test-ratio", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--keep-unknown", action="store_true", help="Keep rows where fault_type is Unknown")
    parser.add_argument("--keep-other", action="store_true", help="Keep rows where fault_type is Other")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows, labels = load_rows(args.csv, drop_unknown=not args.keep_unknown, drop_other=not args.keep_other)
    rows, labels = collapse_rare_labels(rows, labels)
    if not rows:
        raise ValueError("No rows left after filtering labels and empty problem values.")

    classifier, feature_pipeline, class_names, history, train_count, val_count, feature_count = train_and_track(
        rows=rows,
        labels=labels,
        epochs=args.epochs,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    save_model(args.model_out, feature_pipeline, classifier, class_names)
    plot_saved = save_plot(history, args.plot_out)

    final = history[-1]
    print()
    print(f"Train rows: {train_count} | Validation rows: {val_count}")
    print(f"Classes: {len(class_names)} | Features: {feature_count}")
    print(f"Final train accuracy: {final['train_accuracy']:.4f}")
    print(f"Final validation accuracy: {final['val_accuracy']:.4f}")
    print(f"Saved model to: {args.model_out}")
    if plot_saved:
        print(f"Saved plot to: {args.plot_out}")
    else:
        print("matplotlib is not installed, so the PNG plot was not generated yet.")
        print("Install it with: python3 -m pip install matplotlib")


if __name__ == "__main__":
    main()
