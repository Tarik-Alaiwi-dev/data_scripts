import os
import uuid
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsMapSettings,
    QgsMapRendererCustomPainterJob,
    QgsMapLayer,
)
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import QSize, Qt
from qgis.utils import iface
from PyQt5.QtGui import QImage, QPainter

ROOT_DIR = Path("C:/Users/karol/Desktop/qgis")
place_id = str(uuid.uuid4())[:8]

RASTER_OUT_DIR_ZABUDOWANE = ROOT_DIR / f"zabudowane/zdjecia/{place_id}/"
VECTOR_OUT_DIR_ZABUDOWANE = ROOT_DIR / f"zabudowane/mapy/{place_id}/"
RASTER_OUT_DIR_NIEZABUDOWANE = ROOT_DIR / f"niezabudowane/zdjecia/{place_id}/"
VECTOR_OUT_DIR_NIEZABUDOWANE = ROOT_DIR / f"niezabudowane/mapy/{place_id}/"

RASTER_OUT_DIR_ZABUDOWANE.mkdir(parents=True, exist_ok=False)
VECTOR_OUT_DIR_ZABUDOWANE.mkdir(parents=True, exist_ok=False)
RASTER_OUT_DIR_NIEZABUDOWANE.mkdir(parents=True, exist_ok=False)
VECTOR_OUT_DIR_NIEZABUDOWANE.mkdir(parents=True, exist_ok=False)


def get_ordered_layers():
    """Zwraca listę warstw w kolejności z panelu warstw QGIS."""
    root = QgsProject.instance().layerTreeRoot()
    ordered_layers = []

    def collect_layers(group):
        for child in group.children():
            if hasattr(child, 'layer') and child.layer() is not None:
                ordered_layers.append(child.layer())
            elif hasattr(child, 'children'):
                collect_layers(child)

    collect_layers(root)
    return ordered_layers


def render_views(output_folder_vectors, output_folder_rasters, layer_name, image_width=500, image_height=500):
    grid_layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    # Pobierz warstwy w kolejności z QGIS
    ordered_layers = get_ordered_layers()

    total_features = grid_layer.featureCount()
    progress_dialog = QProgressDialog(
        "Proszę o czekanie...", "Anuluj", 0, total_features, iface.mainWindow())
    progress_dialog.setCancelButtonText("Stop")
    progress_dialog.setWindowTitle("Renderowanie widoków")
    progress_dialog.setLabelText("Proszę o czekanie...")
    progress_dialog.setMaximumSize(400, 100)
    progress_dialog.setAutoReset(False)
    progress_dialog.setAutoClose(False)
    progress_dialog.show()

    progress = 0
    for feature in grid_layer.getFeatures():
        progress += 1
        progress_dialog.setValue(progress)

        if progress_dialog.wasCanceled():
            break

        feature_id = feature.id()
        extent = feature.geometry().boundingBox()
        print(f"Renderowanie oczka ID {feature_id} (Extent: {extent.toString()})")

        vector_layers = [
            lyr for lyr in ordered_layers
            if lyr.type() == QgsMapLayer.VectorLayer and extent.intersects(lyr.extent())
        ]
        raster_layers = [
            lyr for lyr in ordered_layers
            if lyr.type() == QgsMapLayer.RasterLayer and extent.intersects(lyr.extent())
        ]

        if vector_layers:
            render_layer_group(vector_layers, extent, image_width, image_height,
                               output_folder_vectors, feature_id, "vectors")

        if raster_layers:
            render_layer_group(raster_layers, extent, image_width, image_height,
                               output_folder_rasters, feature_id, "rasters")

    progress_dialog.close()


def render_layer_group(layers, extent, width, height, output_folder, feature_id, layer_type):
    map_settings = QgsMapSettings()
    map_settings.setLayers(layers)
    map_settings.setExtent(extent)
    map_settings.setOutputSize(QSize(width, height))
    map_settings.setBackgroundColor(Qt.white)

    image = QImage(QSize(width, height), QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.white)

    painter = QPainter(image)
    render_job = QgsMapRendererCustomPainterJob(map_settings, painter)
    render_job.start()
    render_job.waitForFinished()
    painter.end()

    output_path = os.path.join(output_folder, f"cell_{feature_id}.png")
    image.save(output_path)
    print(f"Zapisano obraz {layer_type} dla ID: {feature_id}")


# Uruchom renderowanie
render_views(VECTOR_OUT_DIR_ZABUDOWANE, RASTER_OUT_DIR_ZABUDOWANE, "zabudowane")
render_views(VECTOR_OUT_DIR_NIEZABUDOWANE, RASTER_OUT_DIR_NIEZABUDOWANE, "niezabudowane")
