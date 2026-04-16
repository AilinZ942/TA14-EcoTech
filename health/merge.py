import pandas as pd
import os
import sys

# ==========================================
# STEP 1: File paths
# ==========================================
folder_path = "/Users/jashwanthreddymokilla/Desktop/ecotech/TA14-EcoTech-main/health"
input_file = os.path.join(folder_path, "acimcombinedcounts.csv")

cancer_output = os.path.join(folder_path, "final_cleaned_cancer_data.csv")
mortality_output = os.path.join(folder_path, "final_cleaned_mortality_data.csv")
merged_output = os.path.join(folder_path, "final_health_merged_dataset.csv")
summary_output = os.path.join(folder_path, "health_pipeline_summary.csv")
log_output = os.path.join(folder_path, "pipeline_log.txt")

# ==========================================
# STEP 2: Logger
# ==========================================
log_file = open(log_output, "w", encoding="utf-8")

class Logger:
    def __init__(self, file):
        self.terminal = sys.stdout
        self.file = file

    def write(self, message):
        self.terminal.write(message)
        if not self.file.closed:
            self.file.write(message)

    def flush(self):
        self.terminal.flush()
        if not self.file.closed:
            self.file.flush()

sys.stdout = Logger(log_file)

# ==========================================
# STEP 3: Check input
# ==========================================
if not os.path.exists(folder_path):
    raise FileNotFoundError(f"Folder not found: {folder_path}")

if not os.path.exists(input_file):
    raise FileNotFoundError(f"Input file not found: {input_file}")

print("Input file found:", input_file)

# ==========================================
# STEP 4: Load ACIM file
# ==========================================
df = pd.read_csv(input_file, encoding="utf-8", low_memory=False)
print("Original shape:", df.shape)

# ==========================================
# STEP 5: Clean column names
# ==========================================
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace("-", "_", regex=False)
    .str.replace(r"[^\w_]", "", regex=True)
)

print("Columns after cleaning:", df.columns.tolist())

required_cols = {"year", "sex", "type", "cancer_type"}
missing_required = required_cols - set(df.columns)
if missing_required:
    raise ValueError(f"Missing required columns: {missing_required}")

# ==========================================
# STEP 6: Clean key columns
# ==========================================
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

df["sex"] = (
    df["sex"]
    .astype(str)
    .str.strip()
    .str.lower()
    .replace({
        "female": "females",
        "male": "males",
        "person": "persons",
        "females": "females",
        "males": "males",
        "persons": "persons"
    })
)

df["type"] = df["type"].astype(str).str.strip().str.lower()
df["cancer_type"] = df["cancer_type"].astype(str).str.strip()

# remove blank cancer types
df = df[df["cancer_type"] != ""].copy()

print("Shape after key cleaning:", df.shape)
print("Unique type values:", sorted(df["type"].dropna().unique().tolist()))
print("Unique sex values:", sorted(df["sex"].dropna().unique().tolist()))

# ==========================================
# STEP 7: Find age columns and calculate total_count
# ==========================================
age_cols = [col for col in df.columns if col.startswith("age_")]

if not age_cols:
    raise ValueError("No age_ columns found in ACIM file.")

print("Age columns found:", len(age_cols))

for col in age_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["total_count"] = df[age_cols].sum(axis=1)

# Drop meaningless rows
df = df[df["total_count"] > 0].copy()

print("Shape after total_count filter:", df.shape)
print("Year range:", df["year"].min(), "to", df["year"].max())

# Keep only needed columns
df = df[["year", "sex", "type", "cancer_type", "total_count"]].copy()

# ==========================================
# STEP 8: Split into incidence and mortality
# ==========================================
incidence_df = df[df["type"] == "incidence"].copy()
mortality_df = df[df["type"] == "mortality"].copy()

print("Incidence raw rows:", len(incidence_df))
print("Mortality raw rows:", len(mortality_df))

if incidence_df.empty:
    raise ValueError("No incidence rows found after cleaning.")

if mortality_df.empty:
    raise ValueError("No mortality rows found after cleaning.")

incidence_df = incidence_df.rename(columns={"total_count": "cancer_cases"})
mortality_df = mortality_df.rename(columns={"total_count": "cancer_deaths"})

incidence_df = incidence_df[["year", "sex", "cancer_type", "cancer_cases"]]
mortality_df = mortality_df[["year", "sex", "cancer_type", "cancer_deaths"]]

# ==========================================
# STEP 9: Aggregate duplicates
# ==========================================
incidence_df = (
    incidence_df.groupby(["year", "sex", "cancer_type"], as_index=False)["cancer_cases"]
    .sum()
    .sort_values(["year", "sex", "cancer_type"])
    .reset_index(drop=True)
)

mortality_df = (
    mortality_df.groupby(["year", "sex", "cancer_type"], as_index=False)["cancer_deaths"]
    .sum()
    .sort_values(["year", "sex", "cancer_type"])
    .reset_index(drop=True)
)

# Remove zero or negative values again for safety
incidence_df = incidence_df[incidence_df["cancer_cases"] > 0].copy()
mortality_df = mortality_df[mortality_df["cancer_deaths"] > 0].copy()

print("Incidence cleaned rows:", len(incidence_df))
print("Mortality cleaned rows:", len(mortality_df))

# ==========================================
# STEP 10: Save separate cleaned files
# ==========================================
incidence_df.to_csv(cancer_output, index=False)
mortality_df.to_csv(mortality_output, index=False)

print("Saved:", cancer_output)
print("Saved:", mortality_output)

# ==========================================
# STEP 11: Merge incidence and mortality
# ==========================================
merged_df = pd.merge(
    incidence_df,
    mortality_df,
    on=["year", "sex", "cancer_type"],
    how="inner"
)

print("Merged rows before ratio cleaning:", len(merged_df))

# Derived metric
merged_df["fatality_ratio"] = merged_df["cancer_deaths"] / merged_df["cancer_cases"]

# Clean impossible values
merged_df = merged_df.replace([float("inf"), -float("inf")], pd.NA)
merged_df = merged_df.dropna(subset=["fatality_ratio"])

# Optional: round ratio
merged_df["fatality_ratio"] = merged_df["fatality_ratio"].round(6)

# ==========================================
# STEP 12: Save merged file
# ==========================================
merged_df.to_csv(merged_output, index=False)
print("Saved:", merged_output)

# ==========================================
# STEP 13: Save summary
# ==========================================
summary = pd.DataFrame([{
    "incidence_rows": len(incidence_df),
    "mortality_rows": len(mortality_df),
    "merged_rows": len(merged_df),
    "year_min": int(df["year"].min()) if not df.empty else None,
    "year_max": int(df["year"].max()) if not df.empty else None,
    "sex_count": incidence_df["sex"].nunique() if not incidence_df.empty else 0,
    "cancer_type_count": incidence_df["cancer_type"].nunique() if not incidence_df.empty else 0
}])

summary.to_csv(summary_output, index=False)
print("Saved:", summary_output)
print(summary)

print("\nMerged preview:")
print(merged_df.head())

print("\nSaved log:", log_output)

# ==========================================
# STEP 14: Restore stdout and close log safely
# ==========================================
sys.stdout = sys.__stdout__
log_file.close()