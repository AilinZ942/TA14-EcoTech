# MSSQL GeoJSON Loader

This folder implements the "GeoJSON -> WKT CSV -> MSSQL" workflow.

Files:

- `export_geojson_to_wkt_csv.py`
  Converts the two GeoJSON files into CSV files with a `geometry_wkt` column.
- `import_to_mssql.sql`
  Creates staging tables and final MSSQL tables, then converts WKT into `geometry`.
- `import_csv_with_entra.py`
  Imports the generated CSV files into Azure SQL using a Microsoft Entra access token
  from Azure CLI. No database password is required.
- `output/`
  Generated CSV files.

## Source files

- `/Users/pcw/Downloads/vic_lga_gda2020.geojson`
- `/Users/pcw/Downloads/vic_loc_gda2020.geojson`

## Run the converter

```bash
python3 /Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/mssql_geojson_loader/export_geojson_to_wkt_csv.py
```

## Output CSV files

- `output/vic_lga_gda2020_wkt.csv`
- `output/vic_loc_gda2020_wkt.csv`

## Import into MSSQL

Recommended options:

1. Azure Data Studio Import Wizard
2. `bcp`
3. `SqlBulkCopy`
4. `BULK INSERT` from Azure Blob storage if your SQL environment supports it

Then run:

- `import_to_mssql.sql`

The script first loads CSV rows into staging tables, then converts `geometry_wkt`
into SQL Server `geometry` using:

```sql
geometry::STGeomFromText(geometry_wkt, 7844)
```

## Notes

- Source data is GDA2020, so the SQL script uses SRID `7844`.
- The generated CSV files can be large because polygon geometry is stored as WKT text.
- Azure SQL Database often cannot read local files directly with `BULK INSERT`, so
  Azure Data Studio import or `bcp` is usually easier.

## Passwordless Python import with Entra ID

Install prerequisites:

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18
python3 -m pip install pyodbc
az login
```

Update these values in `import_csv_with_entra.py`:

- `SERVER`
- `DATABASE`

Run in this order:

```bash
python3 /Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/mssql_geojson_loader/export_geojson_to_wkt_csv.py
python3 /Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/mssql_geojson_loader/import_csv_with_entra.py
```

How it works:

- `az account get-access-token --resource https://database.windows.net/`
- Python passes that access token to ODBC
- `pyodbc` connects to Azure SQL without a database password

Important:

- Your Entra user must already have permission in the target Azure SQL database.
- The staging and final tables from `import_to_mssql.sql` must already exist.
