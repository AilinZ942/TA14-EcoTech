-- Azure SQL / MSSQL table for:
--   /Users/pcw/Downloads/maptiler_geocode_cache.json
-- Target schema:
--   dbo
--
-- This JSON file is a dictionary where:
--   key   = cache key / normalized query string
--   value = full MapTiler geocoding response object

IF OBJECT_ID('dbo.maptiler_geocode_cache', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.maptiler_geocode_cache (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        cache_key NVARCHAR(200) NOT NULL,
        response_type NVARCHAR(50) NULL,
        attribution NVARCHAR(500) NULL,
        query_json NVARCHAR(MAX) NULL,
        features_json NVARCHAR(MAX) NULL,
        raw_response_json NVARCHAR(MAX) NOT NULL,

        CONSTRAINT CK_maptiler_geocode_cache_query_json
            CHECK (query_json IS NULL OR ISJSON(query_json) = 1),
        CONSTRAINT CK_maptiler_geocode_cache_features_json
            CHECK (features_json IS NULL OR ISJSON(features_json) = 1),
        CONSTRAINT CK_maptiler_geocode_cache_raw_response_json
            CHECK (ISJSON(raw_response_json) = 1)
    );
END;
GO
