-- Azure SQL schema for:
--   vic_loc_gda2020.geojson

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'spatial')
BEGIN
    EXEC('CREATE SCHEMA spatial');
END;
GO

IF OBJECT_ID('dbo.vic_locality_boundaries', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.vic_locality_boundaries (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        dt_create DATE NULL,
        lc_ply_pid NVARCHAR(100) NOT NULL,
        loc_class NVARCHAR(255) NULL,
        loc_name NVARCHAR(255) NOT NULL,
        loc_pid NVARCHAR(100) NOT NULL,
        state NVARCHAR(10) NOT NULL,
        geom geometry NOT NULL
    );
END;
GO
