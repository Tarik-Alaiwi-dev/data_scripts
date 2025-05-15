import os
import uuid
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsVectorLayer,
    QgsFeature,
    QgsSpatialIndex,
    QgsFillSymbol,  # Add this import
)
# from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, QVariant, Qt
from PyQt5.QtWidgets import QProgressDialog
from qgis.utils import iface
from qgis import processing

# CHANGE
ROOT_DIR = Path(r"C:\Users\karol\Desktop\qgis")
STYLES = {
    "gis_osm_buildings_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_buildings_a_free_1.qml")),
    "gis_osm_landuse_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_landuse_a_free_1.qml")),
    "gis_osm_natural_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_natural_a_free_1.qml")),
    "gis_osm_places_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_places_a_free_1.qml")),
    "gis_osm_pofw_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_pofw_a_free_1.qml")),
    "gis_osm_pois_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_pois_a_free_1.qml")),
    "gis_osm_railways_free_1": str(ROOT_DIR/Path("styles/gis_osm_railways_free_1.qml")),
    "gis_osm_roads_free_1": str(ROOT_DIR/Path("styles/gis_osm_roads_free_1.qml")),
    "gis_osm_traffic_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_traffic_a_free_1.qml")),
    "gis_osm_transport_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_transport_a_free_1.qml")),
    "gis_osm_water_a_free_1": str(ROOT_DIR/Path("styles/gis_osm_water_a_free_1.qml")),
    "gis_osm_waterways_free_1": str(ROOT_DIR/Path("styles/gis_osm_waterways_free_1.qml")),
}
BUILDINGS_LAYER_NAME = "gis_osm_buildings_a_free_1"
GRID_LAYER_NAME = "Siatka"


def analyze_grid():
    """Classifies grid cells into zabudowane (>5% buildings) and niezabudowane (≥3 layers, no buildings)"""
    # Get input layers
    buildings_layer = None
    for layer in QgsProject.instance().mapLayers().values():
        if "gis_osm_buildings_a_free_1" in layer.name():
            buildings_layer = layer
            break
    
    if not buildings_layer:
        raise ValueError("Could not find buildings layer containing 'gis_osm_buildings_a_free_1' in its name")
    
    grid_layer = QgsProject.instance().mapLayersByName("Siatka")[0]

    # Create spatial index for buildings
    building_index = QgsSpatialIndex()
    for feat in buildings_layer.getFeatures():
        building_index.addFeature(feat)

    # Create output layers
    zabudowane_layer = QgsVectorLayer(
        f"Polygon?crs={grid_layer.crs().toWkt()}", 
        "zabudowane", 
        "memory"
    )
    niezabudowane_layer = QgsVectorLayer(
        f"Polygon?crs={grid_layer.crs().toWkt()}", 
        "niezabudowane", 
        "memory"
    )

    # Set transparent styling
    transparent_symbol = QgsFillSymbol.createSimple({
        'color': '0,0,0,0',  # Fully transparent
    })
    zabudowane_layer.renderer().setSymbol(transparent_symbol)
    niezabudowane_layer.renderer().setSymbol(transparent_symbol)

    # Copy fields from original grid
    for layer in [zabudowane_layer, niezabudowane_layer]:
        layer.dataProvider().addAttributes(grid_layer.fields())
        layer.updateFields()

    # Progress dialog
    progress = QProgressDialog("Classifying grid cells...", "Cancel", 0, grid_layer.featureCount())
    progress.setWindowModality(Qt.WindowModal)
    progress.show()

    # Process each grid cell
    for i, grid_feature in enumerate(grid_layer.getFeatures()):
        if progress.wasCanceled():
            break

        grid_geom = grid_feature.geometry()
        grid_area = grid_geom.area()

        # Calculate building coverage
        building_area = 0
        for building_id in building_index.intersects(grid_geom.boundingBox()):
            building_feat = buildings_layer.getFeature(building_id)
            if grid_geom.intersects(building_feat.geometry()):
                building_area += grid_geom.intersection(building_feat.geometry()).area()
        
        building_percent = (building_area / grid_area) * 100 if grid_area > 0 else 0

        # Check for niezabudowane condition (≥3 layers, no buildings)
        intersecting_layers = set()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.extent().intersects(grid_geom.boundingBox()):
                intersecting_layers.add(layer.name())

        # Classify the cell
        new_feat = QgsFeature(zabudowane_layer.fields() if building_percent > 5 
                             else niezabudowane_layer.fields())
        new_feat.setGeometry(grid_geom)
        new_feat.setAttributes(grid_feature.attributes())
        
        if building_percent > 5:
            zabudowane_layer.dataProvider().addFeature(new_feat)
        elif len(intersecting_layers) >= 3 and building_percent == 0:
            niezabudowane_layer.dataProvider().addFeature(new_feat)

        progress.setValue(i + 1)

    # Add layers to project
    QgsProject.instance().addMapLayer(zabudowane_layer)
    QgsProject.instance().addMapLayer(niezabudowane_layer)
    
    return zabudowane_layer, niezabudowane_layer


def reorder_layers(preferred_order, grid_layer_name):
    """Zmiana kolejności warstw w projekcie"""
    root = QgsProject.instance().layerTreeRoot()
    layers = QgsProject.instance().mapLayers().values()
    
    vector_layers = [layer for layer in layers if layer.type() == QgsMapLayer.VectorLayer]
    raster_layers = [layer for layer in layers if layer.type() == QgsMapLayer.RasterLayer]
    
    ordered_layers = []
    
    # Dodawanie warstw w określonej kolejności
    for layer in vector_layers:
        if grid_layer_name.lower() in layer.name().lower():
            ordered_layers.append(layer)
            
    for layer_name in preferred_order:
        for layer in vector_layers:
            if layer_name.lower() in layer.name().lower() and layer not in ordered_layers:
                ordered_layers.append(layer)

    for layer in vector_layers:
        if layer not in ordered_layers:
            ordered_layers.append(layer)

    ordered_layers.extend(raster_layers)

    # Aktualizacja kolejności w drzewie warstw
    for layer in reversed(ordered_layers):
        node = root.findLayer(layer.id())
        if node:
            clone = node.clone()
            parent = node.parent()
            parent.insertChildNode(0, clone)
            parent.removeChildNode(node)

def apply_styles(styles):
    """Aplikacja stylów do warstw"""
    layers = QgsProject.instance().mapLayers().values()
    
    for layer in layers:
        layer_name = layer.name().lower()
        for key, style_path in styles.items():
            if key in layer_name:
                if os.path.exists(style_path):
                    success = layer.loadNamedStyle(style_path)
                    if success[1]:
                        layer.triggerRepaint()
                        print(f"Zastosowano styl dla warstwy: {layer_name}")
                    else:
                        print(f"Nie udało się załadować stylu dla warstwy: {layer_name}")
                else:
                    print(f"Nie znaleziono pliku stylu: {style_path}")
    
    iface.mapCanvas().refresh()
    print("Zakończono aplikację stylów.")

def get_layer_containing(substr):
    layer = None
    for layer in QgsProject.instance().mapLayers().values():
        if substr in layer.name():
            layer = layer
            break
    if layer is None:
        raise ValueError(f"Nie znaleziono warstwy zawierającej '{layer}' w nazwie")
    return layer

def move_layer_to_top(layer):
    """Przenosi warstwę na samą górę w panelu warstw"""
    root = QgsProject.instance().layerTreeRoot()
    node = root.findLayer(layer.id())
    if node:
        clone = node.clone()
        parent = node.parent()
        parent.insertChildNode(0, clone)
        parent.removeChildNode(node)

def remove_unwanted_layers(preferred_order):
    """Removes all layers except those specified in preferred_order (including 'zabudowane' and 'niezabudowane')"""
    project = QgsProject.instance()
    layers_to_remove = []
    
    for layer in project.mapLayers().values():
        # Only keep layers that match names in preferred_order
        if not any(name.lower() in layer.name().lower() for name in preferred_order):
            layers_to_remove.append(layer.id())
    
    # Remove the unwanted layers (including "Siatka")
    for layer_id in layers_to_remove:
        project.removeMapLayer(layer_id)
    
    print(f"Removed {len(layers_to_remove)} unwanted layers")


def main():    

    preferred_order = [     
        "Siatka",
        "zabudowane",
        "niezabudowane",
        "gis_osm_roads_free_1",
        "gis_osm_waterways_free_1",
        "gis_osm_railways_free_1",
        "gis_osm_pois_a_free_1",
        "gis_osm_pofw_a_free_1",
        "gis_osm_traffic_a_free_1",
        "gis_osm_transport_a_free_1",
        "gis_osm_places_a_free_1",
        "gis_osm_buildings_a_free_1",
        "gis_osm_water_a_free_1",
        "gis_osm_natural_a_free_1",
        "gis_osm_landuse_a_free_1"
    ]

    # 1. Run analysis first
    analyze_grid()

    # 4. Now remove unwanted layers
    remove_unwanted_layers(preferred_order)
    
    # Zmiana kolejności warstw
    print("Zmiana kolejności warstw...")
    reorder_layers(preferred_order, GRID_LAYER_NAME)
    
    # Aplikacja stylów
    print("Aplikowanie stylów...")
    apply_styles(STYLES)
    
    # Odświeżenie widoku
    iface.mapCanvas().refresh()
    

    
    print("Proces zakończony pomyślnie!")


main()