import h3
import json

# 1. GENERAR DATOS H3 (Res 3)
def obtener_geometria_h3():
    cells = h3.get_res0_cells()
    all_ids = set()
    for c in cells:
        all_ids.update(h3.cell_to_children(c, 3))
    
    geometrias = []
    for h_id in all_ids:
        boundary = h3.cell_to_boundary(h_id)
        flat_coords = []
        for lat, lon in boundary:
            flat_coords.extend([lon, lat])
        flat_coords.extend([boundary[0][1], boundary[0][0]])
        geometrias.append({"coords": flat_coords})
    return geometrias

print("Calculando malla H3... un momento.")
datos_h3 = obtener_geometria_h3()

html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.108/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.108/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {{ width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; background: #000; }}
        #ui {{ position: absolute; top: 10px; left: 10px; z-index: 100; background: rgba(20,20,20,0.9); 
               padding: 15px; border-radius: 8px; color: white; font-family: sans-serif; border: 1px solid #701C1C; width: 220px; }}
        .item {{ margin: 10px 0; display: flex; align-items: center; cursor: pointer; font-size: 14px; }}
        input[type="checkbox"] {{ margin-right: 10px; accent-color: #ff4444; }}
        .slider-label {{ display: block; margin-top: 10px; font-size: 12px; color: #aaa; }}
        input[type="range"] {{ width: 100%; accent-color: #701C1C; cursor: pointer; }}
        input[type="color"] {{ border: none; width: 30px; height: 20px; cursor: pointer; background: none; margin-right: 10px; }}
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="ui">
        <strong style="color:#ff4444;">JADO WORLD</strong><br><small>Control de Apariencia</small><hr>
        
        <label class="item"><input type="checkbox" id="checkSat" checked> Satélite Esri</label>
        <label class="item"><input type="checkbox" id="checkNat"> National Geographic</label>
        <label class="item"><input type="checkbox" id="checkLab" checked> Etiquetas</label>
        
        <hr>
        <label class="item" style="color:cyan;"><input type="checkbox" id="checkGrid" checked> MALLA H3</label>
        
        <span class="slider-label">Color de Rejilla:</span>
        <div class="item">
            <input type="color" id="colorPicker" value="#701C1C">
            <span id="hexCode">#701C1C</span>
        </div>

        <span class="slider-label">Grosor de Línea: <span id="valWeight">1</span>px</span>
        <input type="range" id="sliderWeight" min="0.5" max="5" step="0.5" value="1">

        <span class="slider-label">Opacidad: <span id="valAlpha">40</span>%</span>
        <input type="range" id="sliderAlpha" min="0" max="100" step="5" value="40">
    </div>

    <script>
        const hexData = {json.dumps(datos_h3)};
        let polylines = [];

        async function main() {{
            const viewer = new Cesium.Viewer('cesiumContainer', {{
                baseLayerPicker: false, geocoder: false, homeButton: true,
                animation: false, timeline: false, skyAtmosphere: new Cesium.SkyAtmosphere()
            }});

            const layers = viewer.imageryLayers;
            layers.removeAll();

            const layerSat = layers.addImageryProvider(await Cesium.ArcGisMapServerImageryProvider.fromUrl('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'));
            const layerNat = layers.addImageryProvider(await Cesium.ArcGisMapServerImageryProvider.fromUrl('https://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer'));
            const layerLab = layers.addImageryProvider(await Cesium.ArcGisMapServerImageryProvider.fromUrl('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer'));
            layerNat.show = false;

            // --- FUNCIÓN PARA ACTUALIZAR LA MALLA ---
            function updateGridStyle() {{
                const colorHex = document.getElementById('colorPicker').value;
                const weight = parseFloat(document.getElementById('sliderWeight').value);
                const alpha = parseFloat(document.getElementById('sliderAlpha').value) / 100;
                
                const cesiumColor = Cesium.Color.fromCssColorString(colorHex).withAlpha(alpha);

                polylines.forEach(entity => {{
                    entity.polyline.width = weight;
                    entity.polyline.material = new Cesium.ColorMaterialProperty(cesiumColor);
                }});

                document.getElementById('valWeight').innerText = weight;
                document.getElementById('valAlpha').innerText = Math.round(alpha * 100);
                document.getElementById('hexCode').innerText = colorHex.toUpperCase();
            }}

            // Crear entidades de la malla
            const gridParent = viewer.entities.add(new Cesium.Entity());
            hexData.forEach(h => {{
                const e = viewer.entities.add({{
                    parent: gridParent,
                    polyline: {{
                        positions: Cesium.Cartesian3.fromDegreesArray(h.coords),
                        width: 1,
                        material: Cesium.Color.fromCssColorString('#701C1C').withAlpha(0.4),
                        arcType: Cesium.ArcType.GEODESIC
                    }}
                }});
                polylines.push(e);
            }});

            // Eventos de control
            document.getElementById('checkSat').onchange = (e) => layerSat.show = e.target.checked;
            document.getElementById('checkNat').onchange = (e) => layerNat.show = e.target.checked;
            document.getElementById('checkLab').onchange = (e) => layerLab.show = e.target.checked;
            document.getElementById('checkGrid').onchange = (e) => gridParent.show = e.target.checked;
            
            document.getElementById('colorPicker').oninput = updateGridStyle;
            document.getElementById('sliderWeight').oninput = updateGridStyle;
            document.getElementById('sliderAlpha').oninput = updateGridStyle;

            viewer.camera.setView({{ destination: Cesium.Cartesian3.fromDegrees(0, 20, 15000000.0) }});
        }}

        main();
    </script>
</body>
</html>
"""

with open("JADO_WORLD.html", "w", encoding="utf-8") as f:
    f.write(html_template)
print("¡Archivo generado!.")