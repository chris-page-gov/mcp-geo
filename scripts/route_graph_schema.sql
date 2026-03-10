CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

CREATE SCHEMA IF NOT EXISTS routing;

CREATE TABLE IF NOT EXISTS routing.graph_metadata (
    graph_version TEXT PRIMARY KEY,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    built_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_product TEXT,
    source_release_date DATE,
    source_download_id TEXT,
    source_download_name TEXT,
    source_license TEXT,
    profiles JSONB NOT NULL DEFAULT '["drive","walk","cycle","emergency","multimodal"]'::jsonb,
    node_count BIGINT,
    edge_count BIGINT,
    provenance_path TEXT,
    coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
    notes JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'ready'
);

CREATE TABLE IF NOT EXISTS routing.graph_nodes (
    id BIGINT PRIMARY KEY,
    geom geometry(Point, 4326) NOT NULL,
    modes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]
);

CREATE INDEX IF NOT EXISTS routing_graph_nodes_geom_idx
    ON routing.graph_nodes
    USING GIST (geom);

CREATE TABLE IF NOT EXISTS routing.graph_edges (
    id BIGINT PRIMARY KEY,
    source BIGINT NOT NULL,
    target BIGINT NOT NULL,
    external_id TEXT,
    name TEXT,
    mode TEXT,
    length_m DOUBLE PRECISION,
    cost_drive DOUBLE PRECISION,
    reverse_cost_drive DOUBLE PRECISION,
    cost_walk DOUBLE PRECISION,
    reverse_cost_walk DOUBLE PRECISION,
    cost_cycle DOUBLE PRECISION,
    reverse_cost_cycle DOUBLE PRECISION,
    cost_emergency DOUBLE PRECISION,
    reverse_cost_emergency DOUBLE PRECISION,
    cost_multimodal DOUBLE PRECISION,
    reverse_cost_multimodal DOUBLE PRECISION,
    flags JSONB NOT NULL DEFAULT '{}'::jsonb,
    geom geometry(LineString, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS routing_graph_edges_geom_idx
    ON routing.graph_edges
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS routing_graph_edges_source_idx
    ON routing.graph_edges (source);

CREATE INDEX IF NOT EXISTS routing_graph_edges_target_idx
    ON routing.graph_edges (target);

CREATE INDEX IF NOT EXISTS routing_graph_edges_external_id_idx
    ON routing.graph_edges (external_id);

CREATE TABLE IF NOT EXISTS routing.edge_restrictions (
    id BIGSERIAL PRIMARY KEY,
    restriction_id TEXT,
    edge_id BIGINT NOT NULL REFERENCES routing.graph_edges(id) ON DELETE CASCADE,
    category TEXT,
    severity TEXT,
    message TEXT,
    penalty_factor DOUBLE PRECISION,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS routing_edge_restrictions_edge_idx
    ON routing.edge_restrictions (edge_id);

CREATE TABLE IF NOT EXISTS routing.turn_restrictions (
    id BIGSERIAL PRIMARY KEY,
    from_edge BIGINT NOT NULL REFERENCES routing.graph_edges(id) ON DELETE CASCADE,
    to_edge BIGINT NOT NULL REFERENCES routing.graph_edges(id) ON DELETE CASCADE,
    via_node BIGINT REFERENCES routing.graph_nodes(id) ON DELETE SET NULL,
    restriction_type TEXT,
    message TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS routing_turn_restrictions_pair_idx
    ON routing.turn_restrictions (from_edge, to_edge);
