from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
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


def compute_state_pearson(state_df: pd.DataFrame) -> pd.DataFrame:
    correlation_rows: list[dict[str, object]] = []

    for waste_metric in WASTE_METRICS:
        for env_metric in ENVIRONMENTAL_METRICS:
            pair = state_df[[waste_metric, env_metric]].dropna()
            n_used = len(pair)
            waste_unique = pair[waste_metric].nunique(dropna=True)
            env_unique = pair[env_metric].nunique(dropna=True)

            if n_used < 2 or waste_unique < 2 or env_unique < 2:
                pearson_corr = None
            else:
                pearson_corr = pair[waste_metric].corr(pair[env_metric], method="pearson")

            correlation_rows.append(
                {
                    "waste_metric": waste_metric,
                    "environmental_metric": env_metric,
                    "n_years_used": n_used,
                    "pearson_corr": pearson_corr,
                }
            )

    correlation_df = pd.DataFrame(correlation_rows)
    correlation_df["abs_pearson_corr"] = correlation_df["pearson_corr"].abs()
    return correlation_df


def build_heatmap_matrix(correlation_df: pd.DataFrame) -> pd.DataFrame:
    matrix = correlation_df.pivot(
        index="waste_metric",
        columns="environmental_metric",
        values="pearson_corr",
    )
    return matrix.loc[WASTE_METRICS, [metric for metric in ENVIRONMENTAL_METRICS if metric in matrix.columns]]


def save_heatmap(state: str, heatmap_matrix: pd.DataFrame, output_path: Path) -> None:
    fig_width = max(14, len(heatmap_matrix.columns) * 0.45)
    fig_height = 3.8
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    image = ax.imshow(heatmap_matrix.fillna(0).values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(len(heatmap_matrix.columns)))
    ax.set_xticklabels(heatmap_matrix.columns, rotation=75, ha="right", fontsize=8)
    ax.set_yticks(range(len(heatmap_matrix.index)))
    ax.set_yticklabels(heatmap_matrix.index, fontsize=9)
    ax.set_title(f"{state} Pearson Correlation Heatmap", fontsize=12)

    for row_idx, row_name in enumerate(heatmap_matrix.index):
        for col_idx, col_name in enumerate(heatmap_matrix.columns):
            value = heatmap_matrix.loc[row_name, col_name]
            label = "NA" if pd.isna(value) else f"{value:.2f}"
            ax.text(
                col_idx,
                row_idx,
                label,
                ha="center",
                va="center",
                fontsize=7,
                color="black",
            )

    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Pearson correlation coefficient", rotation=90)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    data_dir = resolve_data_dir()
    output_dir = data_dir / "state_heatmaps"
    output_dir.mkdir(exist_ok=True)

    df = pd.read_csv(data_dir / "merged_stage1.csv")
    required_columns = {"state", "year_label", *WASTE_METRICS, *ENVIRONMENTAL_METRICS}
    missing_columns = sorted(required_columns.difference(df.columns))
    assert not missing_columns, f"Missing required columns: {missing_columns}"

    all_states_output: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for state, state_df in df.groupby("state"):
        state_df = state_df.sort_values("year_label").copy()
        correlation_df = compute_state_pearson(state_df)
        correlation_df.insert(0, "state", state)
        correlation_df.insert(1, "n_years_total", len(state_df))
        all_states_output.append(correlation_df)

        heatmap_matrix = build_heatmap_matrix(correlation_df)
        save_heatmap(state, heatmap_matrix, output_dir / f"{state}_pearson_heatmap.png")

        ewaste_corr = correlation_df[
            correlation_df["waste_metric"] == "ewaste_proxy_tonnes"
        ].dropna(subset=["pearson_corr"])
        if not ewaste_corr.empty:
            strongest = ewaste_corr.sort_values(
                ["abs_pearson_corr", "environmental_metric"], ascending=[False, True]
            ).iloc[0]
            summary_rows.append(
                {
                    "state": state,
                    "n_years_total": len(state_df),
                    "top_environmental_metric_for_ewaste": strongest["environmental_metric"],
                    "top_pearson_corr_for_ewaste": strongest["pearson_corr"],
                }
            )

    pearson_long = pd.concat(all_states_output, ignore_index=True)
    pearson_summary = pd.DataFrame(summary_rows).sort_values("state")

    pearson_long.to_csv(data_dir / "state_pearson_correlation_long.csv", index=False)
    pearson_summary.to_csv(data_dir / "state_pearson_correlation_summary.csv", index=False)

    print(f"Input shape: {df.shape}")
    print(f"Pearson long table shape: {pearson_long.shape}")
    print(f"Pearson summary shape: {pearson_summary.shape}")
    print(f"Heatmaps saved to: {output_dir}")
    print("\nTop Pearson correlation for ewaste_proxy_tonnes by state:")
    print(pearson_summary.to_string(index=False))


if __name__ == "__main__":
    main()
