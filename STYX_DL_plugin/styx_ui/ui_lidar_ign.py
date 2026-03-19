from PyQt5.QtWidgets import (QComboBox, QDoubleSpinBox, QMessageBox, QDialog,
                             QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
                             QLabel, QFileDialog, QTextEdit, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from qgis.gui import QgsExtentWidget
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsRasterLayer
import os
import math
from qgis import processing
import requests


class Ui_IGN_DEM_DL(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.worker = None
        self.setWindowTitle("BDD Lidar IGN")

        self.base_mnt_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"
        self.base_mns_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"
        self.base_mnh_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"

        self.layout = QVBoxLayout(self)

        # --- Combo: data type ---
        self.comb_to_use = QComboBox()
        self.comb_to_use.addItems(["MNS", "MNT", "MNH"])
        self.add_line('Données à télécharger', self.comb_to_use)

        # --- Resolution ---
        self.res_input = QDoubleSpinBox()
        self.res_input.setMinimum(0.0)
        self.res_input.setMaximum(100000000.0)
        self.res_input.setSingleStep(0.01)
        self.res_input.setProperty("value", 0.5)
        self.add_line('Résolution [m/pxl]', self.res_input)

        # --- Extent ---
        self.extent_widget = QgsExtentWidget(self)
        self.extent_widget.setMapCanvas(self.iface.mapCanvas())
        target_crs = QgsCoordinateReferenceSystem("EPSG:2154")
        default_extent = iface.mapCanvas().extent()
        self.extent_widget.setOriginalExtent(default_extent, iface.mapCanvas().mapSettings().destinationCrs())
        self.extent_widget.setOutputCrs(target_crs)
        self.add_line('Extent', self.extent_widget)

        # --- Save path ---
        self.add_save_option()

        # --- Progress bar (tile level) ---
        self.add_line('')
        self.tile_progress_label = QLabel('Tuiles : 0 / 0')
        self.layout.addWidget(self.tile_progress_label)

        self.tile_progress_bar = QProgressBar()
        self.tile_progress_bar.setValue(0)
        self.tile_progress_bar.setTextVisible(True)
        self.layout.addWidget(self.tile_progress_bar)

        # --- Progress bar (byte level for current tile) ---
        self.byte_progress_label = QLabel('Téléchargement en cours…')
        self.layout.addWidget(self.byte_progress_label)

        self.byte_progress_bar = QProgressBar()
        self.byte_progress_bar.setValue(0)
        self.byte_progress_bar.setTextVisible(True)
        self.layout.addWidget(self.byte_progress_bar)

        # --- Log ---
        self.add_line('')
        self.add_line('>>> Log')
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.create_footer_buttons()
        self.setLayout(self.layout)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def add_save_option(self):
        save_layout = QVBoxLayout()
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText('path')
        self.save_path_button = QPushButton('...')
        self.save_path_button.clicked.connect(self.select_save_path_file)

        save_layout.addWidget(QLabel('Chemin de sauvegarde'))
        row = QHBoxLayout()
        row.addWidget(self.save_path_edit)
        row.addWidget(self.save_path_button)
        save_layout.addLayout(row)
        self.layout.addLayout(save_layout)

    def select_save_path_file(self):
        self.output_layer, _ = QFileDialog.getSaveFileName(
            self, "Save tif file", "", "tif (*.tif)")
        if self.output_layer:
            self.save_path_edit.setText(self.output_layer)

    def add_line(self, label=None, default_data=None):
        row_layout = QHBoxLayout()
        if label is not None:
            row_layout.addWidget(QLabel(label))
        if default_data is not None:
            row_layout.addWidget(default_data)
        self.layout.addLayout(row_layout)

    def create_footer_buttons(self):
        button_layout = QHBoxLayout()

        self.ok_button = QPushButton('OK')
        self.cancel_dl_button = QPushButton('Annuler le téléchargement')
        self.cancel_dl_button.setEnabled(False)
        self.cancel_dl_button.setStyleSheet("color: red;")
        close_button = QPushButton('Fermer')

        self.ok_button.clicked.connect(self.on_ok_button_clicked)
        self.cancel_dl_button.clicked.connect(self.on_cancel_download)
        close_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_dl_button)
        button_layout.addWidget(close_button)
        self.layout.addLayout(button_layout)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def on_cancel_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log_text.append('Annulation..')
            self.cancel_dl_button.setEnabled(False)

    def on_download_finished(self):
        self.ok_button.setEnabled(True)
        self.cancel_dl_button.setEnabled(False)
        self.byte_progress_label.setText('Téléchargement terminé.')

    def on_tile_progress(self, current, total):
        self.tile_progress_label.setText(f'Tuiles : {current} / {total}')
        self.tile_progress_bar.setMaximum(total)
        self.tile_progress_bar.setValue(current)

    def on_byte_progress(self, downloaded_kb, total_kb, tile_index):
        if total_kb > 0:
            pct = int(downloaded_kb * 100 / total_kb)
            self.byte_progress_bar.setMaximum(100)
            self.byte_progress_bar.setValue(pct)
            self.byte_progress_label.setText(
                f'Tuile {tile_index} : {downloaded_kb:.0f} Ko / {total_kb:.0f} Ko  ({pct}%)')
        else:
            # Content-Length unknown — show indeterminate + KB downloaded
            self.byte_progress_bar.setMaximum(0)   # indeterminate mode
            self.byte_progress_bar.setValue(0)
            self.byte_progress_label.setText(
                f'Tuile {tile_index} : {downloaded_kb:.0f} Ko téléchargés…')

    # ------------------------------------------------------------------
    # Main action
    # ------------------------------------------------------------------

    def on_ok_button_clicked(self):
        save_path = self.save_path_edit.text()
        if not save_path:
            QMessageBox.warning(self, "Nope !", "Chemin de sauvegarde manquant")
            return

        extent = self.extent_widget.outputExtent()
        x_min = round(extent.xMinimum(), 2)
        x_max = extent.xMaximum()
        y_min = round(extent.yMinimum(), 2)
        y_max = extent.yMaximum()

        res = self.res_input.value()
        x_max = ((x_max - x_min) // res + 1) * res + x_min
        y_max = ((y_max - y_min) // res + 1) * res + y_min

        target_x_shape = int((x_max - x_min) / res)
        target_y_shape = int((y_max - y_min) / res)

        dl_suffix = []
        save_name = []
        if (target_x_shape < 5000) and (target_y_shape < 5000):
            dl_suffix.append(f"&BBOX={x_min},{y_min},{x_max},{y_max}&WIDTH={target_x_shape}&HEIGHT={target_y_shape}")
            save_name.append(os.path.basename(save_path))
        else:
            tile_on_x = math.ceil(target_x_shape / 5000)
            tile_on_y = math.ceil(target_y_shape / 5000)
            size_m_max = res * 5000

            for i in range(tile_on_x):
                x_min_tile = x_min + i * size_m_max
                x_max_tile = min(x_min + (i + 1) * size_m_max, x_max)
                tile_width = min(5000, target_x_shape - i * 5000)

                for j in range(tile_on_y):
                    y_min_tile = y_min + j * size_m_max
                    y_max_tile = min(y_min + (j + 1) * size_m_max, y_max)
                    tile_height = min(5000, target_y_shape - j * 5000)

                    dl_suffix.append(
                        f"&BBOX={x_min_tile},{y_min_tile},{x_max_tile},{y_max_tile}&WIDTH={tile_width}&HEIGHT={tile_height}")
                    save_name.append(f"{i}_{j}_{os.path.basename(save_path)}")

        data_to_use = self.comb_to_use.currentText()
        if data_to_use == 'MNS':
            base_ign = self.base_mns_uri
        elif data_to_use == 'MNT':
            base_ign = self.base_mnt_uri
        else:
            base_ign = self.base_mnh_uri

        # Reset UI state
        self.tile_progress_bar.setValue(0)
        self.byte_progress_bar.setValue(0)
        self.byte_progress_bar.setMaximum(100)
        self.tile_progress_label.setText(f'Tuiles : 0 / {len(dl_suffix)}')
        self.byte_progress_label.setText('En attente de réponse du serveur IGN…')
        self.ok_button.setEnabled(False)
        self.cancel_dl_button.setEnabled(True)

        self.worker = DownloadWorker(base_ign, dl_suffix, save_name, save_path)
        self.worker.log_signal.connect(self.log_text.append)
        self.worker.tile_progress_signal.connect(self.on_tile_progress)
        self.worker.byte_progress_signal.connect(self.on_byte_progress)
        self.worker.finished_signal.connect(self.on_download_finished)
        self.worker.start()


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    # (tiles_done, tiles_total)
    tile_progress_signal = pyqtSignal(int, int)
    # (downloaded_kb, total_kb, tile_index)  — total_kb == 0 means unknown
    byte_progress_signal = pyqtSignal(float, float, int)
    finished_signal = pyqtSignal()

    CHUNK_SIZE = 65536   # 64 KB — large chunks for faster streaming

    def __init__(self, base_ign, dl_suffix, save_name, save_path):
        super().__init__()
        self.base_ign = base_ign
        self.dl_suffix = dl_suffix
        self.save_name = save_name
        self.save_path = save_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        self.log_signal.emit('Début du téléchargement')
        saved_raster = []
        dir_save = os.path.dirname(self.save_path)
        total = len(self.dl_suffix)

        session = requests.Session()  # reuse TCP connections

        for i, suffix in enumerate(self.dl_suffix):
            if self._cancelled:
                self.log_signal.emit('─────── Téléchargement annulé ───────')
                self.finished_signal.emit()
                return

            full_uri = self.base_ign + suffix + f"&FILENAME={self.save_name[i]}"
            full_save_path = os.path.join(dir_save, self.save_name[i])

            self.tile_progress_signal.emit(i, total)
            self.log_signal.emit(f">> Tuile {i + 1} / {total}")
            self.log_signal.emit(f"   URL : {full_uri}")
            self.log_signal.emit(f"   → {full_save_path}")

            try:
                with session.get(full_uri, stream=True, timeout=120) as r:
                    r.raise_for_status()

                    # Try to get total size from headers
                    content_length = r.headers.get('Content-Length')
                    total_kb = int(content_length) / 1024 if content_length else 0

                    downloaded = 0
                    with open(full_save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=self.CHUNK_SIZE):
                            if self._cancelled:
                                break
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                self.byte_progress_signal.emit(
                                    downloaded / 1024, total_kb, i + 1)

                if self._cancelled:
                    # Remove partial file
                    if os.path.exists(full_save_path):
                        os.remove(full_save_path)
                    self.log_signal.emit('─────── Téléchargement annulé ───────')
                    self.finished_signal.emit()
                    return

                saved_raster.append(full_save_path)
                self.log_signal.emit(f"   OK ({downloaded / 1024:.0f} Ko)")

            except requests.RequestException as e:
                self.log_signal.emit(f"   Erreur : {e}")
                continue

        self.tile_progress_signal.emit(total, total)

        if len(saved_raster) == 0:
            self.log_signal.emit('Aucun fichier téléchargé.')
        elif len(saved_raster) == 1:
            QgsProject.instance().addMapLayer(
                QgsRasterLayer(saved_raster[0],
                               os.path.basename(saved_raster[0]).replace('.tif', '')))
            self.log_signal.emit('Couche ajoutée à QGIS.')
        else:
            self.log_signal.emit('Construction du VRT…')
            vrt_process = processing.run("gdal:buildvirtualraster", {
                'INPUT': saved_raster,
                'RESOLUTION': 0,
                'SEPARATE': False,
                'PROJ_DIFFERENCE': False,
                'ADD_ALPHA': False,
                'ASSIGN_CRS': None,
                'RESAMPLING': 0,
                'SRC_NODATA': '',
                'EXTRA': '',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
            QgsProject.instance().addMapLayer(
                QgsRasterLayer(vrt_process['OUTPUT'],
                               os.path.basename(self.save_path).replace('.tif', '')))
            self.log_signal.emit('VRT ajouté à QGIS.')

        self.finished_signal.emit()