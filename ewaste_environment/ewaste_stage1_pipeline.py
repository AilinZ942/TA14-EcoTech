from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


STATE_MAP = {
    "ACT": "ACT",
    "AUSTRALIAN CAPITAL TERRITORY": "ACT",
    "NSW": "NSW",
    "NEW SOUTH WALES": "NSW",
    "NT": "NT",
    "NORTHERN TERRITORY": "NT",
    "QLD": "QLD",
    "QUEENSLAND": "QLD",
    "Qld": "QLD",
    "SA": "SA",
    "SOUTH AUSTRALIA": "SA",
    "TAS": "TAS",
    "Tas": "TAS",
    "TASMANIA": "TAS",
    "VIC": "VIC",
    "Vic": "VIC",
    "VICTORIA": "VIC",
    "WA": "WA",
    "WESTERN AUSTRALIA": "WA",
}

VALID_STATES = {"ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"}

WASTE_COLUMNS = {
    "Year": "year_raw",
    "Jurisdiction": "state",
    "Category": "waste_category",
    "Type": "waste_type",
    "Classification": "classification",
    "Stream": "stream",
    "Management": "management",
    "Fate": "fate",
    "Tonnes": "tonnes",
}

EMISSIONS_COLUMNS = {
    "report_year": "year_raw",
    "state": "state",
    "substance_name": "substance_name",
    "air_total_emission_kg": "air_total_emission_kg",
    "water_emission_kg": "water_emission_kg",
    "land_emission_kg": "land_emission_kg",
    "facility_id": "facility_id",
    "facility_name": "facility_name",
    "primary_anzsic_class_name": "industry_name",
}

POLLUTANT_PATTERNS = {
    "lead": [r"\blead\b"],
    "mercury": [r"\bmercury\b"],
    "cadmium": [r"\bcadmium\b"],
    "nickel": [r"\bnickel\b"],
    "chromium": [r"\bchromium\b"],
    "copper": [r"\bcopper\b"],
    "zinc": [r"\bzinc\b"],
    "tvoc": [r"total volatile organic compounds"],
    "pm10": [r"\bpm10\b", r"particulate matter.*pm10"],
    "pm25": [r"\bpm2\.5\b", r"pm 2\.5", r"particulate matter.*pm2\.5"],
}


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_DIR / "raw_data"


def resolve_data_dir() -> Path:
    if (RAW_DATA_DIR / "national-waste-database-2022.xlsx").exists() and (
        RAW_DATA_DIR / "emissions.xlsx"
    ).exists():
        return RAW_DATA_DIR
    raise FileNotFoundError(f"Could not locate the required Excel workbooks in {RAW_DATA_DIR}.")


def trim_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def standardise_state(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    mapped = STATE_MAP.get(text)
    if mapped in VALID_STATES:
        return mapped
    text_upper = text.upper()
    mapped = STATE_MAP.get(text_upper)
    if mapped in VALID_STATES:
        return mapped
    return text_upper if text_upper in VALID_STATES else None


def harmonise_year_label(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    match = re.search(r"(\d{4})\s*[-/]\s*(\d{4})", text)
    if not match:
        return None
    start_year, end_year = match.groups()
    return f"{start_year}-{end_year}"


def inspect_frame(label: str, df: pd.DataFrame) -> None:
    print(f"\n[{label}] shape: {df.shape}")
    print(f"[{label}] columns: {list(df.columns)}")


def safe_display(value: object) -> str:
    return str(value).encode("ascii", errors="replace").decode("ascii")


def load_inputs(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    waste_path = data_dir / "national-waste-database-2022.xlsx"
    emissions_path = data_dir / "emissions.xlsx"

    waste_raw = pd.read_excel(waste_path, sheet_name="Database 2022")
    emissions_raw = pd.read_excel(emissions_path, sheet_name="Emissions")

    inspect_frame("waste_raw", waste_raw)
    inspect_frame("emissions_raw", emissions_raw)
    return waste_raw, emissions_raw


def clean_waste_dataset(
    waste_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    waste = waste_raw[list(WASTE_COLUMNS.keys())].rename(columns=WASTE_COLUMNS).copy()
    waste = trim_text_columns(waste)

    waste["state"] = waste["state"].map(standardise_state)
    waste["year_label"] = waste["year_raw"].map(harmonise_year_label)
    waste["tonnes"] = pd.to_numeric(waste["tonnes"], errors="coerce")

    waste = waste.dropna(subset=["state", "year_label", "tonnes"]).copy()
    waste = waste[waste["state"].isin(VALID_STATES)].copy()

    hazardous_proxy = waste[
        waste["waste_category"].fillna("").str.casefold() == "hazardous wastes"
    ].copy()

    waste_state_year_agg = (
        hazardous_proxy.groupby(["state", "year_label"], as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "ewaste_proxy_tonnes": group["tonnes"].sum(),
                    "hazardous_recycling_tonnes": group.loc[
                        group["fate"].fillna("").str.casefold() == "recycling", "tonnes"
                    ].sum(),
                    "hazardous_disposal_tonnes": group.loc[
                        group["fate"].fillna("").str.casefold() == "disposal", "tonnes"
                    ].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
        .sort_values(["state", "year_label"])
    )

    waste_stream_management_breakdown = (
        hazardous_proxy.groupby(
            ["state", "year_label", "stream", "management"], dropna=False, as_index=False
        )["tonnes"]
        .sum()
        .rename(columns={"tonnes": "proxy_tonnes"})
        .sort_values(["state", "year_label", "stream", "management"])
    )

    assert set(waste_state_year_agg.columns) == {
        "state",
        "year_label",
        "ewaste_proxy_tonnes",
        "hazardous_recycling_tonnes",
        "hazardous_disposal_tonnes",
    }
    return waste, hazardous_proxy, waste_state_year_agg, waste_stream_management_breakdown


def match_pollutants(substance_series: pd.Series) -> dict[str, list[str]]:
    matched: dict[str, list[str]] = {}
    unique_substances = substance_series.dropna().astype(str).str.strip().unique()
    for canonical_name, patterns in POLLUTANT_PATTERNS.items():
        hits = []
        for substance in unique_substances:
            substance_lower = substance.lower()
            if any(re.search(pattern, substance_lower, flags=re.IGNORECASE) for pattern in patterns):
                hits.append(substance)
        matched[canonical_name] = sorted(set(hits))
    return matched


def clean_emissions_dataset(
    emissions_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    emissions = emissions_raw[list(EMISSIONS_COLUMNS.keys())].rename(columns=EMISSIONS_COLUMNS).copy()
    emissions = trim_text_columns(emissions)

    emissions["state"] = emissions["state"].map(standardise_state)
    emissions["year_label"] = emissions["year_raw"].map(harmonise_year_label)

    emission_value_columns = [
        "air_total_emission_kg",
        "water_emission_kg",
        "land_emission_kg",
    ]
    for column in emission_value_columns:
        emissions[column] = pd.to_numeric(emissions[column], errors="coerce").fillna(0)

    emissions = emissions.dropna(subset=["state", "year_label", "substance_name"]).copy()
    emissions = emissions[emissions["state"].isin(VALID_STATES)].copy()

    emissions_state_year_substance = (
        emissions.groupby(["state", "year_label", "substance_name"], as_index=False)
        .agg(
            air_total_emission_kg_sum=("air_total_emission_kg", "sum"),
            water_emission_kg_sum=("water_emission_kg", "sum"),
            land_emission_kg_sum=("land_emission_kg", "sum"),
            facility_count=("facility_id", pd.Series.nunique),
        )
        .sort_values(["state", "year_label", "substance_name"])
    )

    matched_pollutants = match_pollutants(emissions_state_year_substance["substance_name"])
    for canonical_name, hits in matched_pollutants.items():
        safe_hits = [safe_display(hit) for hit in hits]
        print(
            f"Matched pollutant '{canonical_name}': "
            f"{safe_hits if safe_hits else 'None'}"
        )

    totals = (
        emissions.groupby(["state", "year_label"], as_index=False)
        .agg(
            total_air_emission_kg=("air_total_emission_kg", "sum"),
            total_water_emission_kg=("water_emission_kg", "sum"),
            total_land_emission_kg=("land_emission_kg", "sum"),
        )
        .sort_values(["state", "year_label"])
    )

    emissions_state_year_wide = totals.copy()

    measure_map = {
        "air": "air_total_emission_kg_sum",
        "water": "water_emission_kg_sum",
        "land": "land_emission_kg_sum",
    }

    for canonical_name, hits in matched_pollutants.items():
        if not hits:
            continue
        subset = emissions_state_year_substance[
            emissions_state_year_substance["substance_name"].isin(hits)
        ].copy()
        for suffix, source_column in measure_map.items():
            wide_piece = (
                subset.groupby(["state", "year_label"], as_index=False)[source_column]
                .sum()
                .rename(columns={source_column: f"{canonical_name}_{suffix}_kg"})
            )
            emissions_state_year_wide = emissions_state_year_wide.merge(
                wide_piece, on=["state", "year_label"], how="left"
            )

    emissions_state_year_wide = emissions_state_year_wide.fillna(0).sort_values(
        ["state", "year_label"]
    )

    return emissions, emissions_state_year_substance, emissions_state_year_wide, matched_pollutants


def attempt_merge(
    waste_state_year_agg: pd.DataFrame, emissions_state_year_wide: pd.DataFrame
) -> pd.DataFrame | None:
    waste_years = sorted(waste_state_year_agg["year_label"].dropna().unique().tolist())
    emissions_years = sorted(emissions_state_year_wide["year_label"].dropna().unique().tolist())
    waste_states = sorted(waste_state_year_agg["state"].dropna().unique().tolist())
    emissions_states = sorted(emissions_state_year_wide["state"].dropna().unique().tolist())

    overlapping_states = sorted(set(waste_states).intersection(emissions_states))
    overlapping_years = sorted(set(waste_years).intersection(emissions_years))

    print("\nUnique waste year_label values:", waste_years)
    print("Unique emissions year_label values:", emissions_years)
    print("Overlapping states:", overlapping_states)
    print("Overlapping year_label values:", overlapping_years)

    if not overlapping_states or not overlapping_years:
        print(
            "\nNo valid shared year window exists after year harmonisation. "
            "Stage-1 correlation should not be run yet."
        )
        return None

    merged = waste_state_year_agg.merge(
        emissions_state_year_wide, on=["state", "year_label"], how="inner"
    )
    print(f"\nMerged shape: {merged.shape}")
    print("Merged missing-value summary:")
    print(merged.isna().sum().to_string())
    return merged


def save_outputs(
    output_dir: Path,
    waste_state_year_agg: pd.DataFrame,
    emissions_state_year_substance: pd.DataFrame,
    emissions_state_year_wide: pd.DataFrame,
    merged_stage1: pd.DataFrame | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    waste_state_year_agg.to_csv(output_dir / "waste_state_year_agg.csv", index=False)
    emissions_state_year_substance.to_csv(
        output_dir / "emissions_state_year_substance.csv", index=False
    )
    emissions_state_year_wide.to_csv(output_dir / "emissions_state_year_wide.csv", index=False)
    if merged_stage1 is not None:
        merged_stage1.to_csv(output_dir / "merged_stage1.csv", index=False)


def print_summary(
    hazardous_proxy: pd.DataFrame,
    matched_pollutants: dict[str, list[str]],
    merged_stage1: pd.DataFrame | None,
) -> None:
    retained_pollutants = [name for name, hits in matched_pollutants.items() if hits]
    print("\nInterpretation summary:")
    print(
        "- E-waste proxy used: Category == 'Hazardous wastes' "
        f"({len(hazardous_proxy):,} hazardous rows retained before aggregation)."
    )
    print(
        "- Pollutants retained: "
        + (", ".join(retained_pollutants) if retained_pollutants else "None of the candidate pollutants were present.")
    )
    print(
        "- Valid merge possible: "
        + ("Yes" if merged_stage1 is not None and not merged_stage1.empty else "No")
    )


def main() -> None:
    data_dir = resolve_data_dir()
    print(f"Using raw data directory: {data_dir}")
    print(f"Writing outputs to: {SCRIPT_DIR}")

    waste_raw, emissions_raw = load_inputs(data_dir)
    _, hazardous_proxy, waste_state_year_agg, waste_stream_management_breakdown = clean_waste_dataset(
        waste_raw
    )
    _, emissions_state_year_substance, emissions_state_year_wide, matched_pollutants = (
        clean_emissions_dataset(emissions_raw)
    )

    print(f"\nWaste state-year aggregate shape: {waste_state_year_agg.shape}")
    print(
        "Optional waste stream-management breakdown shape: "
        f"{waste_stream_management_breakdown.shape}"
    )
    print(f"Emissions state-year-substance shape: {emissions_state_year_substance.shape}")
    print(f"Emissions state-year-wide shape: {emissions_state_year_wide.shape}")

    merged_stage1 = attempt_merge(waste_state_year_agg, emissions_state_year_wide)
    save_outputs(
        SCRIPT_DIR,
        waste_state_year_agg,
        emissions_state_year_substance,
        emissions_state_year_wide,
        merged_stage1,
    )
    print_summary(hazardous_proxy, matched_pollutants, merged_stage1)


if __name__ == "__main__":
    main()
