# LandIS Soil Data Structures

This MCP resource is a concise operational summary of the LandIS soil data
structures paper for implementation and tool-output interpretation.

## Core join model

- NATMAP association polygons identify mapping units using association keys such
  as `MUSID`.
- Association polygons can be expanded into component soil series using the
  `NATMAPassociations` relationship described in LandIS documentation.
- Series-level and horizon-level attributes should be treated as linked lookup
  data rather than attributes that are always directly present on mapping
  polygons.

## Implementation guidance

- Keep polygon screening tools explicit about whether they return association
  classes, derived summaries, or component-series expansion.
- Preserve provenance for the association layer, join table, and any series or
  horizon attribute tables used in a response.
- Do not collapse generalized polygon outputs into site-certainty claims.

## Source

- LandIS. "Soil data structures and relationships."
  `https://www.landis.org.uk/downloads/downloads/Soil%20Data%20Structures.pdf`
