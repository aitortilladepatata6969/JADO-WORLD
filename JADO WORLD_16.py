import folium
import h3
from folium import Map, TileLayer, GeoJson

# ==========================================================
# CONFIGURACIÓN DE RESOLUCIÓN (Ancho aproximado)
# ==========================================================
# Res 2: ~189 km 
# Res 3: ~71 km  (Seleccionada: equilibrio entre detalle y peso)
# Res 4: ~27 km 
# ==========================================================
RESOLUCION_H3 = 3 

# 1. Crear el mapa base
# Usamos 'no_wrap=True' para evitar que el mapa se repita infinitamente y ensucie la malla
m = Map(location=[20, 0], zoom_start=3, no_wrap=False)

# 2. Añadir capas de ESRI (Satelital y Etiquetas)
TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery", 
    name="Satélite Esri", 
    overlay=False
).add_to(m)

# CAPA 2: Esri National Geographic (Añadida)
TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
    attr='Esri, NatGeo, Garmin, HERE, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',
    name='National Geographic',
    overlay=False
).add_to(m)

TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr="Esri Labels", 
    name="Etiquetas y Fronteras", 
    overlay=True,
    show=True
).add_to(m)

# 3. GENERAR MALLA H3 GLOBAL
res0_cells = h3.get_res0_cells() 
all_hex_ids = set()

for cell in res0_cells:
    all_hex_ids.update(h3.cell_to_children(cell, RESOLUCION_H3))

# 4. CONSTRUIR GEOJSON (Con corrección de líneas horizontales)
features = []
for h_id in all_hex_ids:
    geo_boundary = h3.cell_to_boundary(h_id)
    
    # Extraemos longitudes para verificar si el hexágono cruza el corte del mundo (180°/-180°)
    lngs = [p[1] for p in geo_boundary]
    
    # SOLUCIÓN A LAS LÍNEAS HORIZONTALES:
    # Si la diferencia entre la longitud máxima y mínima es muy grande (>180),
    # significa que el hexágono se "estira" por todo el mapa. Lo saltamos para limpiar la vista.
    if max(lngs) - min(lngs) > 180:
        continue 

    # Convertir a formato GeoJSON [longitud, latitud]
    json_boundary = [[p[1], p[0]] for p in geo_boundary]
    json_boundary.append(json_boundary[0]) # Cerrar el polígono

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [json_boundary]
        },
        "id": h_id,
        "properties": {"hex_id": h_id}
    }
    features.append(feature)

geojson_grid = {"type": "FeatureCollection", "features": features}

# 5. AÑADIR LA CAPA AL MAPA CON ESTILO QGIS
# He puesto el color 'cyan' y un grosor fino para que se vea profesional
GeoJson(
    geojson_grid,
    name=f"Malla Hexagonal (Res {RESOLUCION_H3})",
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#701C1C', 
        'weight': 0.3,
        'fillOpacity': 0.0
    },
    highlight_function=lambda x: {
        'weight': 3, 
        'color': 'white', 
        'fillOpacity': 0.3
    },
    tooltip=folium.GeoJsonTooltip(fields=['hex_id'], aliases=['ID Hexágono:'])
).add_to(m)

# 6. AÑADIR SELECTOR Y GUARDAR
folium.LayerControl(collapsed=False).add_to(m)

archivo_salida = f"JADO_WORLD.html"
m.save(archivo_salida)

print("-" * 30)
print(f"MAPA GENERADO: {archivo_salida}")
print(f"Resolución: {RESOLUCION_H3} (aprox. 75km)")
print(f"Hexágonos procesados: {len(features)}")
print("-" * 30)