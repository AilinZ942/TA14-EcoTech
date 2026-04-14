-- Azure SQL schema for:
--   vic_lga_gda2020.geojson

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'spatial')
BEGIN
    EXEC('CREATE SCHEMA spatial');
END;
GO

IF OBJECT_ID('dbo.vic_lga_boundaries', 'U') IS NULL
BEGIN
    CREATE TABLE spatial.vic_lga_boundaries (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        abb_name NVARCHAR(255) NULL,
        dt_create DATE NULL,
        lga_name NVARCHAR(255) NOT NULL,
        lga_pid NVARCHAR(100) NOT NULL,
        lg_ply_pid NVARCHAR(100) NOT NULL,
        state NVARCHAR(10) NOT NULL,
        geom geometry NOT NULL
    );
END;
GO
