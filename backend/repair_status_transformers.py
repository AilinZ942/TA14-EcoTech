from __future__ import annotations

import sys
from typing import Any, TypeAlias

from sklearn.base import BaseEstimator, TransformerMixin

TEXT_FEATURE = "problem"
CATEGORICAL_FEATURES = ["brand", "age", "fault_type"]

FeatureRow: TypeAlias = dict[str, str]


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


_main_module = sys.modules.get("__main__")
if _main_module is not None:
    setattr(_main_module, "ProblemSelector", ProblemSelector)
    setattr(_main_module, "CategoricalSelector", CategoricalSelector)
