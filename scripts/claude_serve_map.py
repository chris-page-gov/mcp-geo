#!/usr/bin/env python3
"""
Simple web server to serve OS map with API key from environment variable.
Usage: python serve_map.py
Then open: http://localhost:8000
"""

import http.server
import json
import os
import socketserver

PORT = 8000

# The HTML template with placeholder for API key
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV1 3HB - Spon End, Coventry (OS Map)</title>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        #map {{
            width: 100%;
            height: 100vh;
        }}
        .info-box {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
        }}
        .info-box h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
            color: #333;
        }}
        .info-box p {{
            margin: 5px 0;
            font-size: 14px;
            color: #666;
        }}
        .legend {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 13px;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .house {{ background: #3388ff; }}
        .church {{ background: #9b59b6; }}
        .pub {{ background: #e74c3c; }}
        
        .maplibregl-popup-content {{
            padding: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 2001;
        }}
        
        .hidden {{
            display: none;
        }}
        
        #error {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #fee;
            color: #c00;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 2002;
            max-width: 500px;
        }}
    </style>
</head>
<body>
    <div id="loading">Loading map...</div>
    <div id="error" class="hidden"></div>
    
    <div class="info-box">
        <h2>CV1 3HB</h2>
        <p><strong>Spon End, Coventry</strong></p>
        <p>14 properties in this postcode</p>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-dot house"></div>
                <span>Residential (11)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot church"></div>
                <span>Bethel Church (1)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot pub"></div>
                <span>Old Dyers Arms (1)</span>
            </div>
        </div>
    </div>
    
    <div id="map"></div>
    
    <script>
        const OS_API_KEY = {api_key_json};
        
        // Property data
        const properties = [
            {{lat: 52.4079936, lon: -1.5268079, name: "19 Spon End", type: "house"}},
            {{lat: 52.4080207, lon: -1.526837, name: "21 Spon End", type: "house"}},
            {{lat: 52.40803, lon: -1.5268957, name: "23 Spon End", type: "house"}},
            {{lat: 52.4080392, lon: -1.5269544, name: "25 Spon End", type: "house"}},
            {{lat: 52.4082112, lon: -1.5272613, name: "27 Spon End", type: "house"}},
            {{lat: 52.4082205, lon: -1.5273347, name: "29 Spon End", type: "house"}},
            {{lat: 52.4082297, lon: -1.5273934, name: "31 Spon End", type: "house"}},
            {{lat: 52.408248, lon: -1.5274667, name: "33 Spon End", type: "house"}},
            {{lat: 52.4082573, lon: -1.5275401, name: "35 Spon End", type: "house"}},
            {{lat: 52.4082576, lon: -1.5276136, name: "37 Spon End", type: "house"}},
            {{lat: 52.4082489, lon: -1.5276872, name: "39 Spon End", type: "house"}},
            {{lat: 52.4077496, lon: -1.5263934, name: "4A Spon End", type: "house"}},
            {{lat: 52.4078303, lon: -1.5265196, name: "Bethel Church", type: "church"}},
            {{lat: 52.407801, lon: -1.5258544, name: "Old Dyers Arms", type: "pub"}}
        ];
        
        const colors = {{
            house: '#3388ff',
            church: '#9b59b6',
            pub: '#e74c3c'
        }};
        
        function showError(message) {{
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
            document.getElementById('loading').classList.add('hidden');
        }}
        
        function initMap() {{
            if (!OS_API_KEY) {{
                showError('OS_API_KEY environment variable not set. Please set it and restart the server.');
                return;
            }}
            
            if (typeof maplibregl === 'undefined') {{
                showError('MapLibre GL failed to load. Check your internet connection.');
                return;
            }}
            
            try {{
                const map = new maplibregl.Map({{
                    container: 'map',
                    style: `https://api.os.uk/maps/vector/v1/vts/resources/styles?key=${{OS_API_KEY}}`,
                    center: [-1.527, 52.408],
                    zoom: 17,
                    maxZoom: 20
                }});
                
                map.on('load', function() {{
                    document.getElementById('loading').classList.add('hidden');
                    
                    // Add markers
                    properties.forEach(prop => {{
                        const el = document.createElement('div');
                        el.style.backgroundColor = colors[prop.type];
                        el.style.width = '16px';
                        el.style.height = '16px';
                        el.style.borderRadius = '50%';
                        el.style.border = '2px solid white';
                        el.style.cursor = 'pointer';
                        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
                        
                        const popup = new maplibregl.Popup({{ offset: 25 }})
                            .setHTML(`<strong>${{prop.name}}</strong><br>CV1 3HB`);
                        
                        new maplibregl.Marker({{ element: el }})
                            .setLngLat([prop.lon, prop.lat])
                            .setPopup(popup)
                            .addTo(map);
                    }});
                    
                    // Add postcode boundary
                    map.addSource('postcode-boundary', {{
                        'type': 'geojson',
                        'data': {{
                            'type': 'Feature',
                            'geometry': {{
                                'type': 'Polygon',
                                'coordinates': [[
                                    [-1.5277, 52.4077],
                                    [-1.5277, 52.4083],
                                    [-1.5258, 52.4083],
                                    [-1.5258, 52.4077],
                                    [-1.5277, 52.4077]
                                ]]
                            }}
                        }}
                    }});
                    
                    map.addLayer({{
                        'id': 'postcode-boundary-fill',
                        'type': 'fill',
                        'source': 'postcode-boundary',
                        'paint': {{
                            'fill-color': '#f39c12',
                            'fill-opacity': 0.1
                        }}
                    }});
                    
                    map.addLayer({{
                        'id': 'postcode-boundary-line',
                        'type': 'line',
                        'source': 'postcode-boundary',
                        'paint': {{
                            'line-color': '#f39c12',
                            'line-width': 2,
                            'line-dasharray': [2, 2]
                        }}
                    }});
                }});
                
                map.on('error', function(e) {{
                    console.error('Map error:', e);
                    showError('Failed to load map. Check API key and internet connection.');
                }});
                
                map.addControl(new maplibregl.NavigationControl(), 'top-left');
                
            }} catch (error) {{
                console.error('Error:', error);
                showError('Error initializing map: ' + error.message);
            }}
        }}
        
        // Wait for everything to load
        window.addEventListener('load', initMap);
    </script>
</body>
</html>
"""

def get_os_api_key() -> str:
    return os.environ.get("OS_API_KEY", "")


def render_html(api_key: str) -> str:
    return HTML_TEMPLATE.format(api_key_json=json.dumps(api_key))


class MapHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            api_key = get_os_api_key()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = render_html(api_key)
            self.wfile.write(html.encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Customize logging
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    api_key = get_os_api_key()
    if not api_key:
        print("WARNING: OS_API_KEY environment variable is not set!")
        print("The map will not load without a valid API key.")
        print("\nTo set it:")
        print("  export OS_API_KEY='your-key-here'")
        print()
    
    with socketserver.TCPServer(("", PORT), MapHandler) as httpd:
        print(f"Serving CV1 3HB map at http://localhost:{PORT}")
        print(f"API Key {'found' if api_key else 'NOT FOUND'} in environment")
        print(f"\nOpen your browser to: http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    main()
