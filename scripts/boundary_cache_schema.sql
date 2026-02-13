-- PostGIS boundary cache schema for MCP Geo
-- Loads administrative boundary datasets into a unified table with metadata.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS boundary_datasets (
    dataset_id TEXT PRIMARY KEY,
    source TEXT,
    title TEXT,
    url TEXT,
    license TEXT,
    release_date DATE,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    record_count INTEGER,
    checksum TEXT,
    resolution TEXT,
    coverage TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS admin_boundaries (
    id BIGSERIAL PRIMARY KEY,
    area_id TEXT NOT NULL,
    level TEXT NOT NULL,
    name TEXT,
    resolution TEXT NOT NULL,
    resolution_rank INTEGER DEFAULT 0,
    min_zoom INTEGER,
    max_zoom INTEGER,
    dataset_id TEXT REFERENCES boundary_datasets(dataset_id) ON DELETE SET NULL,
    geom geometry(MultiPolygon, 4326),
    bbox geometry(Polygon, 4326),
    centroid geometry(Point, 4326),
    is_valid BOOLEAN,
    valid_reason TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT
);

CREATE INDEX IF NOT EXISTS admin_boundaries_area_id_idx ON admin_boundaries (area_id);
CREATE INDEX IF NOT EXISTS admin_boundaries_level_idx ON admin_boundaries (level);
CREATE INDEX IF NOT EXISTS admin_boundaries_name_idx ON admin_boundaries (name);
CREATE INDEX IF NOT EXISTS admin_boundaries_dataset_idx ON admin_boundaries (dataset_id);
CREATE INDEX IF NOT EXISTS admin_boundaries_geom_gix ON admin_boundaries USING GIST (geom);
