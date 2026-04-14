-- Azure SQL / MSSQL table for:
--   clean_ewaste_facilities_geocoded.csv
-- Target schema:
--   dbo

IF OBJECT_ID('dbo.clean_ewaste_facilities_geocoded', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.clean_ewaste_facilities_geocoded (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        facility_name NVARCHAR(255) NOT NULL,
        address NVARCHAR(255) NULL,
        suburb NVARCHAR(100) NULL,
        postcode NVARCHAR(10) NULL,
        state NVARCHAR(10) NULL,
        latitude FLOAT NULL,
        longitude FLOAT NULL,
        coord_source NVARCHAR(50) NULL,
        duplicate_count INT NULL,
        source_file NVARCHAR(255) NULL,
        source_provenance NVARCHAR(255) NULL,
        ewaste_match_flag BIT NULL,
        ewaste_match_text NVARCHAR(255) NULL,
        ewaste_match_column NVARCHAR(100) NULL,
        review_flag NVARCHAR(255) NULL,
        dedupe_key NVARCHAR(255) NULL,
        original_latitude FLOAT NULL,
        original_longitude FLOAT NULL,
        original_coord_source NVARCHAR(50) NULL,
        maptiler_query NVARCHAR(255) NULL,
        maptiler_place_name NVARCHAR(255) NULL,
        maptiler_match_score FLOAT NULL,
        maptiler_feature_id NVARCHAR(100) NULL
    );
END;
GO
