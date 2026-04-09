import h3
import json

# --- CONFIGURACIÓN ---
RESOLUCION = 3 
ARCHIVO_SALIDA = "JADO_WORLD_30.html"

def generar_pro():
    print(f"Generando hexágonos H3 (Res {RESOLUCION})...")
    
    # 1. GENERAR HEXÁGONOS
    res0_cells = h3.get_res0_cells()
    all_hex_ids = set()
    for cell in res0_cells:
        all_hex_ids.update(h3.cell_to_children(cell, RESOLUCION))

    features = []
    for h_id in all_hex_ids:
        geo_boundary = h3.cell_to_boundary(h_id)
        lngs = [p[1] for p in geo_boundary]
        if max(lngs) - min(lngs) > 180: continue 

        coords = [[p[1], p[0]] for p in geo_boundary]
        coords.append(coords[0]) 
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": {"id": h_id}
        })

    geojson_string = json.dumps({"type": "FeatureCollection", "features": features})

    # 2. HTML CON CONTROLES DE ESTILO (GROSOR Y COLOR)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>JADO WORLD | Pro Customizer</title>
        <meta charset='utf-8'>
        <link rel='stylesheet' href='https://unpkg.com/maplibre-gl@5.0.0/dist/maplibre-gl.css' />
        <script src='https://unpkg.com/maplibre-gl@5.0.0/dist/maplibre-gl.js'></script>
        <style>
            body {{ margin: 0; padding: 0; background: #000; overflow: hidden; font-family: sans-serif; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
            #ui {{
                position: absolute; top: 10px; left: 10px; z-index: 10;
                background: rgba(10, 10, 10, 0.95); color: white; padding: 15px;
                border: 1px solid #701C1C; border-radius: 8px; width: 220px;
            }}
            .section-title {{ font-weight: bold; color: #ff4444; margin-bottom: 8px; font-size: 14px; }}
            .item {{ margin-bottom: 10px; display: flex; align-items: center; font-size: 13px; cursor: pointer; }}
            input[type="radio"], input[type="checkbox"] {{ margin-right: 10px; accent-color: #ff4444; }}
            .control-group {{ margin-top: 10px; border-top: 1px solid #333; padding-top: 10px; }}
            .control-label {{ display: block; font-size: 11px; color: #bbb; margin-bottom: 5px; }}
            input[type="range"] {{ width: 100%; accent-color: #ff4444; cursor: pointer; }}
            input[type="color"] {{ width: 100%; height: 25px; border: none; background: none; cursor: pointer; }}
            hr {{ border: 0; border-top: 1px solid #333; margin: 10px 0; }}
        </style>
    </head>
    <body>
    <div id="ui">
        <div class="section-title">MAPAS BASE</div>
        <label class="item"><input type="radio" name="base" value="nat" checked> National Geographic</label>
        <label class="item"><input type="radio" name="base" value="sat"> Satellite</label>
        
        <div class="control-group">
            <div class="section-title">CAPAS</div>
            <label class="item"><input type="checkbox" id="checkLabels" checked> Etiquetas</label>
            <label class="item"><input type="checkbox" id="checkH3" checked> Malla H3</label>
        </div>

        <div class="control-group">
            <div class="section-title">ESTILO H3</div>
            <span class="control-label">Grosor de línea</span>
            <input type="range" id="h3Width" min="0.1" max="5" step="0.1" value="0.6">
            
            <span class="control-label" style="margin-top:10px;">Color de malla</span>
            <input type="color" id="h3Color" value="#701c1c">
        </div>
    </div>
    <div id="map"></div>
    <script>
        const h3Data = {geojson_string};

        const map = new maplibregl.Map({{
            container: 'map',
            zoom: 2,
            center: [0, 20],
            style: {{
                'version': 8,
                'projection': {{ 'type': 'globe' }},
                'sources': {{
                    'esri-nat': {{ 'type': 'raster', 'tiles': ['https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{{z}}/{{y}}/{{x}}'], 'tileSize': 256 }},
                    'esri-sat': {{ 'type': 'raster', 'tiles': ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}'], 'tileSize': 256 }},
                    'esri-labels': {{ 'type': 'raster', 'tiles': ['https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}'], 'tileSize': 256 }},
                    'h3-source': {{ 'type': 'geojson', 'data': h3Data }}
                }},
                'layers': [
                    {{ 'id': 'ly-nat', 'type': 'raster', 'source': 'esri-nat', 'layout': {{'visibility': 'visible'}} }},
                    {{ 'id': 'ly-sat', 'type': 'raster', 'source': 'esri-sat', 'layout': {{'visibility': 'none'}} }},
                    {{ 'id': 'ly-labels', 'type': 'raster', 'source': 'esri-labels', 'layout': {{'visibility': 'visible'}} }},
                    {{ 
                        'id': 'ly-h3', 'type': 'line', 'source': 'h3-source',
                        'paint': {{ 
                            'line-color': '#701C1C', 
                            'line-width': 0.6 
                        }}
                    }}
                ]
            }}
        }});

        map.on('load', () => {{
            // Selectores de Base
            document.getElementsByName('base').forEach(radio => {{
                radio.onclick = (e) => {{
                    const val = e.target.value;
                    map.setLayoutProperty('ly-nat', 'visibility', val === 'nat' ? 'visible' : 'none');
                    map.setLayoutProperty('ly-sat', 'visibility', val === 'sat' ? 'visible' : 'none');
                }};
            }});

            // Toggles de Capas
            document.getElementById('checkLabels').onchange = (e) => {{
                map.setLayoutProperty('ly-labels', 'visibility', e.target.checked ? 'visible' : 'none');
            }};
            document.getElementById('checkH3').onchange = (e) => {{
                map.setLayoutProperty('ly-h3', 'visibility', e.target.checked ? 'visible' : 'none');
            }};

            // CONTROLES DINÁMICOS DE H3
            document.getElementById('h3Width').oninput = (e) => {{
                map.setPaintProperty('ly-h3', 'line-width', parseFloat(e.target.value));
            }};
            document.getElementById('h3Color').oninput = (e) => {{
                map.setPaintProperty('ly-h3', 'line-color', e.target.value);
            }};
        }});
    </script>
    </body>
    </html>
    """

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"¡Listo! Archivo '{ARCHIVO_SALIDA}' generado con éxito.")

if __name__ == "__main__":
    generar_pro()