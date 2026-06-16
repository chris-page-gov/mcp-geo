# OS NGD Postcode Boundaries For BigQuery

Last checked: 2026-06-16

This note records the API call and coordinate reference system choice for loading
the OS NGD postcode boundary polygons into BigQuery `GEOGRAPHY`.

## Summary

Use the OS NGD API - Features `Postcode Unit Area v1` collection and request
GeoJSON in `CRS84`:

```text
https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/items
```

`CRS84` is WGS84 longitude/latitude order, which is the order expected by
GeoJSON and BigQuery.

## Collection

- Collection ID: `asu-gbpcd-postcodeunitarea-1`
- Title: `Postcode Unit Area v1`
- Product family: OS NGD Administrative and Statistical Units, OS GB Postcodes
- Feature grain: postcode-unit area part
- Storage CRS: `EPSG:27700` British National Grid
- Advertised response CRSs: `EPSG:27700`, `EPSG:3857`, `EPSG:4326`, `CRS84`
- Coverage: Great Britain

OS describes these polygons as notional extents for addresses sharing a postcode
unit, derived from georeferenced Royal Mail PAF delivery addresses. They are for
display and analysis at postcode-unit level; they are not legal or administrative
boundaries.

Important: do not assume one geometry row per postcode. The collection can
return more than one polygon part for a postcode, so dissolve/group by
`postcode` if the downstream model needs one footprint per postcode.

## Discovery Calls

Collection metadata:

```http
GET https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1
```

Queryable fields:

```http
GET https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/queryables
```

Useful queryable fields include:

- `postcode`
- `featureid`
- `postcodearea`
- `postcodedistrict`
- `postcodesector`

Feature schema:

```http
GET https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/schema
```

## BigQuery-Safe Item Requests

Request `CRS84` explicitly:

```bash
curl -H "key: $OS_API_KEY" \
  "https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/items?filter=postcode%3D%27SW1A%201AA%27&limit=100&crs=http%3A%2F%2Fwww.opengis.net%2Fdef%2Fcrs%2FOGC%2F1.3%2FCRS84"
```

The same request without URL encoding, for readability:

```text
GET /features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/items
  ?filter=postcode='SW1A 1AA'
  &limit=100
  &crs=http://www.opengis.net/def/crs/OGC/1.3/CRS84
```

Sector or district examples:

```text
filter=postcodesector='SW1A 1'
filter=postcodedistrict='SW1A'
```

Keep `limit` at or below the OS API page limit. Follow `next` links in the
GeoJSON response for paged extracts.

## Loading To BigQuery

Store the raw FeatureCollection or one feature per row first, then create a
persisted `GEOGRAPHY` column from each feature's `geometry` object:

```sql
SELECT
  JSON_VALUE(feature, '$.properties.postcode') AS postcode,
  JSON_VALUE(feature, '$.properties.featureid') AS featureid,
  ST_GEOGFROMGEOJSON(TO_JSON_STRING(JSON_QUERY(feature, '$.geometry'))) AS geom
FROM source_rows;
```

If the raw feature is held as a JSON string, parse it first:

```sql
SELECT
  JSON_VALUE(PARSE_JSON(feature_json), '$.properties.postcode') AS postcode,
  ST_GEOGFROMGEOJSON(
    TO_JSON_STRING(JSON_QUERY(PARSE_JSON(feature_json), '$.geometry'))
  ) AS geom
FROM source_rows;
```

Create one dissolved geometry per postcode when required:

```sql
SELECT
  postcode,
  ST_UNION_AGG(geom) AS geom
FROM postcode_unit_area_parts
GROUP BY postcode;
```

Cluster persisted BigQuery tables by the `GEOGRAPHY` column where spatial joins
or containment queries are common.

## Why CRS84, Not Bare EPSG:4326

`EPSG:4326` and `CRS84` both refer to WGS84 longitude/latitude values in common
web mapping language, but they are not identical labels in strict OGC usage.

The EPSG registry defines `EPSG:4326` as an ellipsoidal 2D coordinate system with
axes `latitude, longitude`. GeoJSON and OGC API - Features Core use WGS84 in
longitude/latitude order. RFC 7946 states that GeoJSON positions are longitude,
latitude and identifies the CRS as OGC `CRS84`.

For BigQuery, this matters because BigQuery `GEOGRAPHY` expects points on WGS84
with longitude first and latitude second. Requesting `CRS84` makes that axis
order explicit and avoids ambiguity introduced by the `EPSG:4326` identifier in
strict OGC contexts.

Use:

```text
crs=http://www.opengis.net/def/crs/OGC/1.3/CRS84
```

Avoid requesting this for direct BigQuery ingestion unless a separate
reprojection step is planned:

```text
crs=http://www.opengis.net/def/crs/EPSG/0/27700
```

## References

- OS NGD API - Features root:
  `https://api.os.uk/features/ngd/ofa/v1`
- OS NGD postcode unit collection metadata:
  `https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1`
- OS NGD queryables for postcode unit areas:
  `https://api.os.uk/features/ngd/ofa/v1/collections/asu-gbpcd-postcodeunitarea-1/queryables`
- OS NGD GB Postcodes documentation:
  `https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/gb-postcodes`
- OS NGD Postcode Unit Area documentation:
  `https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/gb-postcodes/postcode-unit-area`
- OS NGD API - Features technical specification:
  `https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-features/technical-specification/features`
- EPSG registry entry for `EPSG:4326`:
  `https://epsg.org/crs_4326/WGS-84.html`
- GeoJSON RFC 7946:
  `https://www.rfc-editor.org/rfc/rfc7946`
- OGC API - Features Part 1: Core:
  `https://docs.ogc.org/is/17-069r3/17-069r3.html`
- OGC API - Features Part 2: Coordinate Reference Systems by Reference:
  `https://docs.ogc.org/is/18-058r1/18-058r1.html`
- BigQuery geospatial data documentation:
  `https://cloud.google.com/bigquery/docs/geospatial-data`
