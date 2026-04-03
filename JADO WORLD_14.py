import folium
import h3
import xml.etree.ElementTree as ET
import random
import math
from folium import Map, TileLayer, GeoJson, Marker, DivIcon

# ==========================================================
# 1. CONFIGURACIÓN DEL WARGAME
# ==========================================================
RESOLUCION_TABLERO = 3  # ~75km (Escala Global)
PROPORCION_FICHA = 0.75 # Las fichas ocupan el 75% del hexágono

# Símbolos FontAwesome para representar tus unidades de Vassal
SIMBOLOS_UNIDADES = [
    '<i class="fa fa-fighter-jet fa-3x" style="color: #FFD700;"></i>',
    '<i class="fa fa-ship fa-3x" style="color: #00BFFF;"></i>',
    '<i class="fa fa-tank fa-3x" style="color: #32CD32;"></i>',
    '<i class="fa fa-satellite-dish fa-3x" style="color: #FF4500;"></i>',
    '<i class="fa fa-rocket fa-3x" style="color: #DC143C;"></i>'
]

# Tu XML de Vassal (puedes cargarlo desde un archivo con ET.parse('tu_archivo.xml'))
vassal_xml_data = """
<root>
    <VASSAL.build.widget.BoxWidget entryName="BAHREIN">
        <VASSAL.build.widget.PieceSlot entryName="BA2__F-16CD" gpid="5665" />
        <VASSAL.build.widget.PieceSlot entryName="BA01__SAM PAC-3" gpid="5840" />
        <VASSAL.build.widget.PieceSlot entryName="FFG90__Perry" gpid="5750" />
        <VASSAL.build.widget.PieceSlot entryName="TF01__(1)" gpid="5670" />
        <VASSAL.build.widget.PieceSlot entryName="FFL01__Manama" gpid="5720" />
        <VASSAL.build.widget.PieceSlot entryName="BALISTICO__M57" gpid="5667" />
        <VASSAL.build.widget.PieceSlot entryName="BA2__AIR BASE" gpid="5664" />
        <VASSAL.build.widget.PieceSlot entryName="ANY__SAM M57" gpid="5800" />
        <VASSAL.build.widget.PieceSlot entryName="MB01__Al-Fateh" gpid="5749" />
        <VASSAL.build.widget.PieceSlot entryName="BA1__RADAR TPS-59" gpid="5799" />
    </VASSAL.build.widget.BoxWidget>
</root>
"""

# ==========================================================
# 2. CREACIÓN DEL MAPA Y CAPAS PROFESIONALES
# ==========================================================
# Centramos el inicio en el Golfo Pérsico (Bahrein)
m = Map(location=[26.1, 50.6], zoom_start=7, control_scale=True)

TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery", name="Satélite Esri", overlay=False
).add_to(m)

TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr="Esri Labels", name="Etiquetas", overlay=True
).add_to(m)

# ==========================================================
# 3. GENERACIÓN DE LA MALLA HEXAGONAL GLOBAL (H3)
# ==========================================================
res0_cells = h3.get_res0_cells()
all_hex_ids = set()
for cell in res0_cells:
    all_hex_ids.update(h3.cell_to_children(cell, RESOLUCION_TABLERO))

features = []
centros_disponibles = []

for h_id in all_hex_ids:
    geo = h3.cell_to_boundary(h_id)
    lngs = [p[1] for p in geo]
    
    # Corrección Antimeridiano (evita líneas horizontales)
    if max(lngs) - min(lngs) > 180:
        continue 

    # Geometría para GeoJSON
    json_boundary = [[p[1], p[0]] for p in geo]
    json_boundary.append(json_boundary[0])

    features.append({
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [json_boundary]},
        "id": h_id
    })
    
    # Guardamos centros cercanos a Bahrein para colocar las fichas del XML
    lat_c, lng_c = h3.cell_to_latlng(h_id)
    if 24 < lat_c < 28 and 48 < lng_c < 53:
        centros_disponibles.append((lat_c, lng_c))

# Añadir la malla al mapa
GeoJson(
    {"type": "FeatureCollection", "features": features},
    name="Malla Global H3 (75km)",
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#00FFFF',
        'weight': 0.8,
        'fillOpacity': 0.0
    },
    highlight_function=lambda x: {'weight': 3, 'color': 'white', 'fillOpacity': 0.1}
).add_to(m)

# ==========================================================
# 4. PARSER DE XML Y COLOCACIÓN DE FICHAS
# ==========================================================
root = ET.fromstring(vassal_xml_data)
unidades = [slot.get('entryName') for slot in root.iter('VASSAL.build.widget.PieceSlot')]

# Tamaño visual de la ficha (ajustado para que sea imponente)
size_px = 100 

random.shuffle(centros_disponibles)

for i, nombre_unidad in enumerate(unidades):
    if i >= len(centros_disponibles): break
    
    posicion = centros_disponibles[i]
    icono_html = random.choice(SIMBOLOS_UNIDADES)
    
    # HTML del "Contenedor" de la ficha (Estilo ficha de wargame)
    html_ficha = f'''
    <div style="
        width: {size_px}px; height: {size_px}px;
        background-color: rgba(255, 255, 255, 0.25);
        border: 3px solid #FFFFFF;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0px 0px 15px rgba(0,0,0,0.7);
        backdrop-filter: blur(2px);
        cursor: move;">
        {icono_html}
    </div>
    '''
    
    Marker(
        location=posicion,
        draggable=True,
        icon=DivIcon(
            icon_size=(size_px, size_px),
            icon_anchor=(size_px/2, size_px/2),
            html=html_ficha
        ),
        tooltip=f"<b>Unidad:</b> {nombre_unidad}<br><i>Arrastra para mover</i>"
    ).add_to(m)

# ==========================================================
# 5. FINALIZACIÓN Y GUARDADO
# ==========================================================
folium.LayerControl(collapsed=False).add_to(m)

nombre_archivo = "wargame_global_h3.html"
m.save(nombre_archivo)

print("-" * 40)
print(f"✅ ¡SISTEMA GENERADO EXITOSAMENTE!")
print(f"🌍 Malla: Todo el mundo (Res 3)")
print(f"🕹️ Fichas cargadas: {len(unidades)}")
print(f"📂 Archivo: {nombre_archivo}")
print("-" * 40)