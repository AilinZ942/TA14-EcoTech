from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_DIR / "raw_data"
EWASTE_ENV_DIR = PROJECT_DIR / "ewaste_environment"


EMISSIONS_HEALTH_ALIGNMENT = "start_year"

STATE_NAME_TO_CODE = {
    "Australian Capital Territory": "ACT",
    "New South Wales": "NSW",
    "Northern Territory": "NT",
    "Queensland": "QLD",
    "South Australia": "SA",
    "Tasmania": "TAS",
    "Victoria": "VIC",
    "Western Australia": "WA",
}

EMISSIONS_METRICS = [
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

HEALTH_METRICS = [
    "deaths",
    "crude_rate_per_100000",
    "age_standardised_rate_per_100000",
    "premature_deaths",
    "premature_deaths_percent",
    "premature_deaths_asr_per_100000",
    "potential_years_of_life_lost",
    "pyll_rate_per_1000",
    "potentially_avoidable_deaths",
    "pad_percent",
    "pad_asr_per_100000",
    "median_age",
]


def resolve_data_dir() -> Path:
    if (EWASTE_ENV_DIR / "emissions_state_year_wide.csv").exists() and (
        RAW_DATA_DIR / "aihw-phe-229-mort-table1-data-gov-au-2025.csv"
    ).exists():
        return SCRIPT_DIR
    raise FileNotFoundError(
        "Could not locate the required emissions and health files in the expected folders."
    )


def parse_financial_year(year_label: str) -> tuple[int | None, int | None]:
    match = re.fullmatch(r"(\d{4})-(\d{4})", str(year_label).strip())
    if not match:
        return None, None
    start_year, end_year = match.groups()
    return int(start_year), int(end_year)


def clean_emissions() -> pd.DataFrame:
    emissions = pd.read_csv(EWASTE_ENV_DIR / "emissions_state_year_wide.csv").copy()

    parsed_years = emissions["year_label"].map(parse_financial_year)
    emissions["start_year"] = parsed_years.map(lambda pair: pair[0])
    emissions["end_year"] = parsed_years.map(lambda pair: pair[1])
    emissions = emissions.dropna(subset=["state", "year_label", "start_year", "end_year"]).copy()
    emissions["start_year"] = emissions["start_year"].astype(int)
    emissions["end_year"] = emissions["end_year"].astype(int)

    missing_columns = sorted(set(EMISSIONS_METRICS).difference(emissions.columns))
    assert not missing_columns, f"Missing emissions columns: {missing_columns}"
    return emissions


def clean_health() -> pd.DataFrame:
    health = pd.read_csv(
        RAW_DATA_DIR / "aihw-phe-229-mort-table1-data-gov-au-2025.csv",
        low_memory=False,
    ).copy()

    health = health[health["category"].astype(str).str.strip() == "State and territory"].copy()
    health = health[health["SEX"].astype(str).str.strip() == "Persons"].copy()
    health["state"] = health["geography"].map(STATE_NAME_TO_CODE)
    health["health_year"] = pd.to_numeric(health["YEAR"], errors="coerce")

    numeric_columns = ["population", *HEALTH_METRICS]
    for column in numeric_columns:
        health[column] = (
            health[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .replace({"nan": pd.NA})
        )
        health[column] = pd.to_numeric(health[column], errors="coerce")

    health = health.dropna(subset=["state", "health_year"]).copy()
    health["health_year"] = health["health_year"].astype(int)

    health_columns = ["state", "health_year", "population", *HEALTH_METRICS]
    health = health[health_columns].sort_values(["state", "health_year"]).reset_index(drop=True)
    return health


def compare_alignment_options(emissions: pd.DataFrame, health: pd.DataFrame) -> None:
    health_keys = set(zip(health["state"], health["health_year"]))
    for alignment in ["start_year", "end_year"]:
        emission_keys = set(zip(emissions["state"], emissions[alignment]))
        overlap = sorted(emission_keys.intersection(health_keys))
        overlap_years = sorted({year for _, year in overlap})
        print(
            f"Alignment option '{alignment}': {len(overlap)} overlapping state-year pairs; "
            f"years={overlap_years}"
        )


def merge_emissions_health(
    emissions: pd.DataFrame, health: pd.DataFrame, alignment: str
) -> pd.DataFrame:
    if alignment not in {"start_year", "end_year"}:
        raise ValueError("alignment must be 'start_year' or 'end_year'")

    merged = emissions.merge(
        health,
        left_on=["state", alignment],
        right_on=["state", "health_year"],
        how="inner",
    ).copy()

    merged["alignment_used"] = alignment
    merged = merged.sort_values(["state", "health_year"]).reset_index(drop=True)
    return merged


def build_pearson_table(merged: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for emissions_metric in EMISSIONS_METRICS:
        for health_metric in HEALTH_METRICS:
            pair = merged[[emissions_metric, health_metric]].dropna()
            n_pairs = len(pair)
            emissions_unique = pair[emissions_metric].nunique(dropna=True)
            health_unique = pair[health_metric].nunique(dropna=True)

            if n_pairs < 2 or emissions_unique < 2 or health_unique < 2:
                pearson_corr = None
            else:
                pearson_corr = pair[emissions_metric].corr(pair[health_metric], method="pearson")

            rows.append(
                {
                    "emissions_metric": emissions_metric,
                    "health_metric": health_metric,
                    "n_state_year_pairs": n_pairs,
                    "pearson_corr": pearson_corr,
                }
            )

    pearson_table = pd.DataFrame(rows)
    pearson_table["abs_pearson_corr"] = pearson_table["pearson_corr"].abs()
    return pearson_table.sort_values(
        ["health_metric", "abs_pearson_corr", "emissions_metric"],
        ascending=[True, False, True],
    )


def build_heatmap_matrix(pearson_table: pd.DataFrame) -> pd.DataFrame:
    matrix = pearson_table.pivot(
        index="health_metric",
        columns="emissions_metric",
        values="pearson_corr",
    )
    return matrix.loc[
        [metric for metric in HEALTH_METRICS if metric in matrix.index],
        [metric for metric in EMISSIONS_METRICS if metric in matrix.columns],
    ]


def save_heatmap(heatmap_matrix: pd.DataFrame, output_path: Path) -> None:
    fig_width = max(14, len(heatmap_matrix.columns) * 0.42)
    fig_height = max(5, len(heatmap_matrix.index) * 0.45)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    image = ax.imshow(heatmap_matrix.fillna(0).values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(len(heatmap_matrix.columns)))
    ax.set_xticklabels(heatmap_matrix.columns, rotation=75, ha="right", fontsize=8)
    ax.set_yticks(range(len(heatmap_matrix.index)))
    ax.set_yticklabels(heatmap_matrix.index, fontsize=8)
    ax.set_title("Emissions vs Health Pearson Correlation Heatmap", fontsize=12)

    for row_idx, row_name in enumerate(heatmap_matrix.index):
        for col_idx, col_name in enumerate(heatmap_matrix.columns):
            value = heatmap_matrix.loc[row_name, col_name]
            label = "NA" if pd.isna(value) else f"{value:.2f}"
            ax.text(col_idx, row_idx, label, ha="center", va="center", fontsize=6.5, color="black")

    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Pearson correlation coefficient", rotation=90)

    plt.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_summary(pearson_table: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []

    for health_metric in HEALTH_METRICS:
        subset = pearson_table[pearson_table["health_metric"] == health_metric].dropna(
            subset=["pearson_corr"]
        )
        if subset.empty:
            continue

        strongest = subset.sort_values(
            ["abs_pearson_corr", "emissions_metric"], ascending=[False, True]
        ).iloc[0]
        summary_rows.append(
            {
                "health_metric": health_metric,
                "top_emissions_metric": strongest["emissions_metric"],
                "top_pearson_corr": strongest["pearson_corr"],
                "n_state_year_pairs": int(strongest["n_state_year_pairs"]),
            }
        )

    return pd.DataFrame(summary_rows).sort_values("health_metric")


def main() -> None:
    data_dir = resolve_data_dir()
    emissions = clean_emissions()
    health = clean_health()

    print(f"Using alignment preference: {EMISSIONS_HEALTH_ALIGNMENT}")
    compare_alignment_options(emissions, health)

    merged = merge_emissions_health(emissions, health, EMISSIONS_HEALTH_ALIGNMENT)
    assert not merged.empty, "No merged state-year pairs found for the selected alignment."

    pearson_table = build_pearson_table(merged)
    heatmap_matrix = build_heatmap_matrix(pearson_table)
    summary = build_summary(pearson_table)

    health.to_csv(data_dir / "health_state_year_persons.csv", index=False)
    merged.to_csv(data_dir / "emissions_health_state_year_merged.csv", index=False)
    pearson_table.to_csv(data_dir / "emissions_health_pearson_long.csv", index=False)
    summary.to_csv(data_dir / "emissions_health_pearson_summary.csv", index=False)
    save_heatmap(heatmap_matrix, data_dir / "emissions_health_pearson_heatmap.png")

    print(f"\nHealth table shape: {health.shape}")
    print(f"Merged emissions-health shape: {merged.shape}")
    print(f"Pearson table shape: {pearson_table.shape}")
    print(f"Summary shape: {summary.shape}")
    print("\nTop emissions correlation for each health metric:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
