## Fixed

- Added explicit MCP-App handoff guidance to `os_apps.render_*` responses so
  clients preserve `ui://` app resources instead of fabricating standalone
  Leaflet/OpenStreetMap/Postcodes.io map artifacts when host rendering is
  unavailable.
