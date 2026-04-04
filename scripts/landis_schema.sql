CREATE SCHEMA IF NOT EXISTS landis;

CREATE TABLE IF NOT EXISTS landis.product_registry (
    product_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    family TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    resource_uri TEXT,
    dataset_version TEXT,
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS landis.dataset_provenance (
    dataset_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_url TEXT,
    license_name TEXT,
    dataset_version TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS landis.soilscapes_polygons (
    feature_id BIGSERIAL PRIMARY KEY,
    class_code TEXT NOT NULL,
    class_name TEXT NOT NULL,
    dominant_texture TEXT,
    drainage_class TEXT,
    carbon_status TEXT,
    habitat_note TEXT,
    scale_label TEXT,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS soilscapes_polygons_geom_idx
    ON landis.soilscapes_polygons
    USING GIST (geom);

CREATE TABLE IF NOT EXISTS landis.pipe_risk_polygons (
    feature_id BIGSERIAL PRIMARY KEY,
    shrink_swell_code TEXT,
    shrink_swell_label TEXT,
    shrink_swell_score INTEGER,
    corrosion_code TEXT,
    corrosion_label TEXT,
    corrosion_score INTEGER,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS pipe_risk_polygons_geom_idx
    ON landis.pipe_risk_polygons
    USING GIST (geom);
