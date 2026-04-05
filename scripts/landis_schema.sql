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

CREATE TABLE IF NOT EXISTS landis.natmap_polygons (
    feature_id BIGSERIAL PRIMARY KEY,
    map_unit_id TEXT,
    map_symbol TEXT,
    map_unit_name TEXT,
    description TEXT,
    geology TEXT,
    dominant_soils TEXT,
    associated_soils TEXT,
    site_class TEXT,
    crop_landuse TEXT,
    soilscape TEXT,
    drainage TEXT,
    fertility TEXT,
    habitats TEXT,
    drains_to TEXT,
    water_protection TEXT,
    soilguide TEXT,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS natmap_polygons_geom_idx
    ON landis.natmap_polygons
    USING GIST (geom);

CREATE TABLE IF NOT EXISTS landis.natmap_thematic_polygons (
    feature_id BIGSERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,
    class_code TEXT,
    class_label TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS natmap_thematic_polygons_geom_idx
    ON landis.natmap_thematic_polygons
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS natmap_thematic_polygons_product_idx
    ON landis.natmap_thematic_polygons (product_id);

CREATE TABLE IF NOT EXISTS landis.nsi_sites (
    feature_id BIGSERIAL PRIMARY KEY,
    nsi_id BIGINT NOT NULL,
    series_name TEXT,
    variant TEXT,
    subgroup TEXT,
    landuse TEXT,
    madeground TEXT,
    rocktype TEXT,
    survey_date TIMESTAMPTZ,
    altitude DOUBLE PRECISION,
    slope TEXT,
    aspect TEXT,
    easting INTEGER,
    northing INTEGER,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS nsi_sites_geom_idx
    ON landis.nsi_sites
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS nsi_sites_nsi_id_idx
    ON landis.nsi_sites (nsi_id);

CREATE TABLE IF NOT EXISTS landis.nsi_observations (
    feature_id BIGSERIAL PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    nsi_id BIGINT NOT NULL,
    observation_label TEXT,
    top_depth_cm DOUBLE PRECISION,
    lower_depth_cm DOUBLE PRECISION,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    dataset_version TEXT,
    source_url TEXT,
    license_name TEXT,
    updated_at TIMESTAMPTZ,
    geom geometry(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS nsi_observations_geom_idx
    ON landis.nsi_observations
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS nsi_observations_nsi_id_idx
    ON landis.nsi_observations (nsi_id);

CREATE INDEX IF NOT EXISTS nsi_observations_dataset_idx
    ON landis.nsi_observations (dataset_id);
