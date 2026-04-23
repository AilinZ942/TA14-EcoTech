from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


WASTE_METRICS = [
    "ewaste_proxy_tonnes",
    "hazardous_recycling_tonnes",
    "hazardous_disposal_tonnes",
]

POLLUTANT_METRICS = [
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


SCRIPT_DIR = Path(__file__).resolve().parent


def resolve_data_dir() -> Path:
    if (SCRIPT_DIR / "merged_stage1.csv").exists():
        return SCRIPT_DIR
    raise FileNotFoundError(f"Could not locate merged_stage1.csv in {SCRIPT_DIR}.")


def aggregate_to_state_totals(df: pd.DataFrame) -> pd.DataFrame:
    aggregate_columns = WASTE_METRICS + POLLUTANT_METRICS
    state_totals = (
        df.groupby("state", as_index=False)[aggregate_columns]
        .sum()
        .sort_values("state")
        .reset_index(drop=True)
    )
    return state_totals


def build_pearson_table(state_totals: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for waste_metric in WASTE_METRICS:
        for pollutant_metric in POLLUTANT_METRICS:
            pair = state_totals[["state", waste_metric, pollutant_metric]].dropna()
            n_states = len(pair)
            waste_unique = pair[waste_metric].nunique(dropna=True)
            pollutant_unique = pair[pollutant_metric].nunique(dropna=True)

            if n_states < 2 or waste_unique < 2 or pollutant_unique < 2:
                pearson_corr = None
            else:
                pearson_corr = pair[waste_metric].corr(pair[pollutant_metric], method="pearson")

            rows.append(
                {
                    "waste_metric": waste_metric,
                    "pollutant_metric": pollutant_metric,
                    "n_states_used": n_states,
                    "pearson_corr": pearson_corr,
                }
            )

    pearson_table = pd.DataFrame(rows)
    pearson_table["abs_pearson_corr"] = pearson_table["pearson_corr"].abs()
    return pearson_table.sort_values(
        ["waste_metric", "abs_pearson_corr", "pollutant_metric"],
        ascending=[True, False, True],
    )


def build_heatmap_matrix(pearson_table: pd.DataFrame) -> pd.DataFrame:
    matrix = pearson_table.pivot(
        index="waste_metric",
        columns="pollutant_metric",
        values="pearson_corr",
    )
    return matrix.loc[WASTE_METRICS, [metric for metric in POLLUTANT_METRICS if metric in matrix.columns]]


def save_heatmap(heatmap_matrix: pd.DataFrame, output_path: Path) -> None:
    fig_width = max(14, len(heatmap_matrix.columns) * 0.45)
    fig_height = 3.8
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    image = ax.imshow(heatmap_matrix.fillna(0).values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(len(heatmap_matrix.columns)))
    ax.set_xticklabels(heatmap_matrix.columns, rotation=75, ha="right", fontsize=8)
    ax.set_yticks(range(len(heatmap_matrix.index)))
    ax.set_yticklabels(heatmap_matrix.index, fontsize=9)
    ax.set_title("Overall State-Aggregated Pearson Correlation Heatmap", fontsize=12)

    for row_idx, row_name in enumerate(heatmap_matrix.index):
        for col_idx, col_name in enumerate(heatmap_matrix.columns):
            value = heatmap_matrix.loc[row_name, col_name]
            label = "NA" if pd.isna(value) else f"{value:.2f}"
            ax.text(col_idx, row_idx, label, ha="center", va="center", fontsize=7, color="black")

    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Pearson correlation coefficient", rotation=90)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_summary(pearson_table: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []

    for waste_metric in WASTE_METRICS:
        subset = pearson_table[pearson_table["waste_metric"] == waste_metric].dropna(
            subset=["pearson_corr"]
        )
        if subset.empty:
            continue

        strongest = subset.sort_values(
            ["abs_pearson_corr", "pollutant_metric"], ascending=[False, True]
        ).iloc[0]
        summary_rows.append(
            {
                "waste_metric": waste_metric,
                "top_pollutant_metric": strongest["pollutant_metric"],
                "top_pearson_corr": strongest["pearson_corr"],
                "n_states_used": int(strongest["n_states_used"]),
            }
        )

    return pd.DataFrame(summary_rows).sort_values("waste_metric")


def main() -> None:
    data_dir = resolve_data_dir()
    df = pd.read_csv(data_dir / "merged_stage1.csv")

    required_columns = {"state", *WASTE_METRICS, *POLLUTANT_METRICS}
    missing_columns = sorted(required_columns.difference(df.columns))
    assert not missing_columns, f"Missing required columns: {missing_columns}"

    state_totals = aggregate_to_state_totals(df)
    pearson_table = build_pearson_table(state_totals)
    summary = build_summary(pearson_table)
    heatmap_matrix = build_heatmap_matrix(pearson_table)

    state_totals.to_csv(data_dir / "state_total_ewaste_pollutants.csv", index=False)
    pearson_table.to_csv(data_dir / "overall_state_aggregate_pearson.csv", index=False)
    summary.to_csv(data_dir / "overall_state_aggregate_pearson_summary.csv", index=False)
    save_heatmap(heatmap_matrix, data_dir / "overall_state_aggregate_pearson_heatmap.png")

    print(f"Input shape: {df.shape}")
    print(f"State-total table shape: {state_totals.shape}")
    print(f"Pearson table shape: {pearson_table.shape}")
    print(f"Summary shape: {summary.shape}")
    print("\nTop Pearson correlation by waste metric after aggregating each state across all years:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
