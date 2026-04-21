from __future__ import annotations

from pathlib import Path

import pandas as pd


WASTE_METRICS = [
    "ewaste_proxy_tonnes",
    "hazardous_recycling_tonnes",
    "hazardous_disposal_tonnes",
]

ENVIRONMENTAL_METRICS = [
    "total_air_emission_kg",
    "total_water_emission_kg",
    "total_land_emission_kg",
    "lead_air_kg",
    "lead_water_kg",
    "lead_land_kg",
    "mercury_air_kg",
    "mercury_water_kg",
    "mercury_land_kg",
    "cadmium_air_kg",
    "cadmium_water_kg",
    "cadmium_land_kg",
    "nickel_air_kg",
    "nickel_water_kg",
    "nickel_land_kg",
    "chromium_air_kg",
    "chromium_water_kg",
    "chromium_land_kg",
    "copper_air_kg",
    "copper_water_kg",
    "copper_land_kg",
    "zinc_air_kg",
    "zinc_water_kg",
    "zinc_land_kg",
    "tvoc_air_kg",
    "tvoc_water_kg",
    "tvoc_land_kg",
    "pm10_air_kg",
    "pm10_water_kg",
    "pm10_land_kg",
    "pm25_air_kg",
    "pm25_water_kg",
    "pm25_land_kg",
]


def resolve_data_dir() -> Path:
    candidates = [Path("/mnt/data"), Path.cwd()]
    for candidate in candidates:
        if (candidate / "merged_stage1.csv").exists():
            return candidate
    raise FileNotFoundError("Could not locate merged_stage1.csv.")


def build_correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for state, state_df in df.groupby("state"):
        state_df = state_df.sort_values("year_label").copy()
        n_years = len(state_df)

        for waste_metric in WASTE_METRICS:
            for env_metric in ENVIRONMENTAL_METRICS:
                pair = state_df[[waste_metric, env_metric]].dropna()
                n_used = len(pair)

                waste_unique = pair[waste_metric].nunique(dropna=True)
                env_unique = pair[env_metric].nunique(dropna=True)

                if n_used < 2 or waste_unique < 2 or env_unique < 2:
                    pearson_corr = None
                    spearman_corr = None
                else:
                    pearson_corr = pair[waste_metric].corr(pair[env_metric], method="pearson")
                    spearman_corr = pair[waste_metric].corr(pair[env_metric], method="spearman")

                records.append(
                    {
                        "state": state,
                        "n_years_total": n_years,
                        "waste_metric": waste_metric,
                        "environmental_metric": env_metric,
                        "n_years_used": n_used,
                        "pearson_corr": pearson_corr,
                        "spearman_corr": spearman_corr,
                    }
                )

    correlations = pd.DataFrame.from_records(records)
    correlations["abs_pearson_corr"] = correlations["pearson_corr"].abs()
    correlations["abs_spearman_corr"] = correlations["spearman_corr"].abs()
    return correlations.sort_values(
        ["state", "waste_metric", "abs_pearson_corr", "environmental_metric"],
        ascending=[True, True, False, True],
    )


def build_state_summary(correlations: pd.DataFrame) -> pd.DataFrame:
    summary_records: list[dict[str, object]] = []

    for state, state_corr in correlations.groupby("state"):
        for waste_metric in WASTE_METRICS:
            subset = state_corr[state_corr["waste_metric"] == waste_metric].copy()
            subset = subset.dropna(subset=["pearson_corr"])
            if subset.empty:
                continue

            top_pearson = subset.sort_values(
                ["abs_pearson_corr", "environmental_metric"], ascending=[False, True]
            ).iloc[0]
            top_spearman = subset.sort_values(
                ["abs_spearman_corr", "environmental_metric"], ascending=[False, True]
            ).iloc[0]

            summary_records.append(
                {
                    "state": state,
                    "waste_metric": waste_metric,
                    "n_years_total": int(top_pearson["n_years_total"]),
                    "top_pearson_metric": top_pearson["environmental_metric"],
                    "top_pearson_corr": top_pearson["pearson_corr"],
                    "top_spearman_metric": top_spearman["environmental_metric"],
                    "top_spearman_corr": top_spearman["spearman_corr"],
                }
            )

    return pd.DataFrame.from_records(summary_records).sort_values(["state", "waste_metric"])


def print_interpretation(summary: pd.DataFrame) -> None:
    print("Per-state correlation analysis completed.")
    print("Method: Pearson and Spearman correlations within each state across shared years.")
    print("Caution: each state has only 15 yearly observations, so treat these as exploratory.")
    print("\nTop absolute Pearson correlation by state for ewaste_proxy_tonnes:")

    ewaste_only = summary[summary["waste_metric"] == "ewaste_proxy_tonnes"].copy()
    for _, row in ewaste_only.iterrows():
        print(
            f"- {row['state']}: {row['top_pearson_metric']} "
            f"(pearson={row['top_pearson_corr']:.3f}, spearman best={row['top_spearman_metric']} "
            f"{row['top_spearman_corr']:.3f})"
        )


def main() -> None:
    data_dir = resolve_data_dir()
    input_path = data_dir / "merged_stage1.csv"

    df = pd.read_csv(input_path)
    required_columns = {"state", "year_label", *WASTE_METRICS, *ENVIRONMENTAL_METRICS}
    missing_columns = sorted(required_columns.difference(df.columns))
    assert not missing_columns, f"Missing required columns: {missing_columns}"

    correlation_table = build_correlation_table(df)
    state_summary = build_state_summary(correlation_table)

    correlation_table.to_csv(data_dir / "state_correlation_long.csv", index=False)
    state_summary.to_csv(data_dir / "state_correlation_summary.csv", index=False)

    print(f"Input shape: {df.shape}")
    print(f"Correlation table shape: {correlation_table.shape}")
    print(f"Summary table shape: {state_summary.shape}")
    print_interpretation(state_summary)


if __name__ == "__main__":
    main()
