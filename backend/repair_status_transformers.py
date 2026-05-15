from __future__ import annotations

from typing import Any, TypeAlias

from sklearn.base import BaseEstimator, TransformerMixin


FeatureRow: TypeAlias = dict[str, str]


TEXT_FEATURE = "problem"
CATEGORICAL_FEATURES = ["brand", "age", "fault_type"]


class ProblemSelector(BaseEstimator, TransformerMixin):
    def fit(self, rows: list[FeatureRow], y: Any = None) -> "ProblemSelector":
        return self

    def transform(self, rows: list[FeatureRow]) -> list[str]:
        return [row[TEXT_FEATURE] for row in rows]


class CategoricalSelector(BaseEstimator, TransformerMixin):
    def fit(self, rows: list[FeatureRow], y: Any = None) -> "CategoricalSelector":
        return self

    def transform(self, rows: list[FeatureRow]) -> list[FeatureRow]:
        return [{key: row[key] for key in CATEGORICAL_FEATURES} for row in rows]
