from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QTextEdit
from qgis.gui import QgsExtentWidget
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import *
import os
import math
from qgis import processing

class Ui_IGN_DEM_DL(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.setWindowTitle("BDD Lidar IGN")

        # liens
        #♦ exemple de liens:
        # https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154&BBOX=701999.75,6521000.25,702999.75,6524000.25&WIDTH=6000&HEIGHT=2000&FILENAME=LHD_FXX_0702_6523_MNT_O_0M50_LAMB93_IGN69.tif
        # https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154&BBOX=708999.75,6761000.25,709999.75,6762000.25&WIDTH=2000&HEIGHT=2000&FILENAME=LHD_FXX_0709_6762_MNS_O_0M50_LAMB93_IGN69.tif
        # https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154&BBOX=546999.75,6525000.25,547999.75,6526000.25&WIDTH=2000&HEIGHT=2000&FILENAME=LHD_FXX_0547_6526_MNH_O_0M50_LAMB93_IGN69.tif

        self.base_mnt_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"
        self.base_mns_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"
        self.base_mnh_uri = "https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&EXCEPTIONS=text/xml&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&FORMAT=image/geotiff&STYLES=&CRS=EPSG:2154"

        # Layout
        self.layout = QVBoxLayout(self)

        self.comb_to_use = QComboBox()

        self.comb_to_use.addItems(["MNS", "MNT", "MNH"])
        self.add_line('Données à télécharger', self.comb_to_use)

        # resolution
         # target resolution input
        self.res_input = QDoubleSpinBox()
        self.res_input.setMinimum(0.0)
        self.res_input.setMaximum(100000000.0)
        self.res_input.setSingleStep(0.01)
        self.res_input.setProperty("value", 0.5)
        
        self.add_line('Résolution [m/pxl]', self.res_input)

        # extent
        self.extent_widget = QgsExtentWidget(self)
        self.extent_widget.setMapCanvas(self.iface.mapCanvas())
        target_crs = QgsCoordinateReferenceSystem("EPSG:2154")
       
        default_extent = iface.mapCanvas().extent()
        self.extent_widget.setOriginalExtent( default_extent, iface.mapCanvas().mapSettings().destinationCrs() )
        self.extent_widget.setOutputCrs( target_crs )

        self.add_line('Extent', self.extent_widget)

        self.add_save_option()

        self.add_line( '' )
        self.add_line( '>>> Log' )
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

       
        self.create_footer_buttons()

        self.setLayout(self.layout)


    
    def add_save_option(self):
        # Path selection button and line edit
        save_layout = QVBoxLayout()

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText('path')
        self.save_path_button = QPushButton('...')
        self.save_path_button.clicked.connect(self.select_save_path_file)

        save_layout.addWidget(QLabel('Chemin de sauvegarde'))
        row_layout_bis = QHBoxLayout()
        row_layout_bis.addWidget(self.save_path_edit)
        row_layout_bis.addWidget(self.save_path_button)
        save_layout.addLayout(row_layout_bis)

        self.layout.addLayout(save_layout)

    def select_save_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        if folder:
            self.save_path_edit.setText(folder)

    def select_save_path_file(self):
        self.output_layer, _ = QFileDialog.getSaveFileName(self, 
                                                         "Save tif file",
                                                         "",
                                                         "tif (*.tif)")
        if self.output_layer:
            self.save_path_edit.setText(self.output_layer)
            
    def add_line(self, label=None, default_data=None):
        row_layout = QHBoxLayout()
        if label is not None:
            label_q = QLabel(label)
            row_layout.addWidget(label_q)
        if default_data is not None:
            row_layout.addWidget(default_data)
        self.layout.addLayout(row_layout)
        
    def create_footer_buttons(self):
        button_layout = QHBoxLayout()
        ok_button = QPushButton('OK')
        cancel_button = QPushButton('Cancel')
        # ok_button.clicked.connect( lambda: call_inference({'config': self.config_manager.current_config}))
        ok_button.clicked.connect( self.on_ok_button_clicked )
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)

    def on_ok_button_clicked(self):
        save_path = self.save_path_edit.text()
        if not save_path:
            QMessageBox.warning(self, "Nope !", "Chemin de sauvegarde manquant")
            return
        
        extent = self.extent_widget.outputExtent() # QgsRectangle
        x_min = round(extent.xMinimum(),2)
        x_max = extent.xMaximum()
        y_min = round(extent.yMinimum(),2)
        y_max = extent.yMaximum()

        # arrondie les coord pour garder la résolution
        res = self.res_input.value()
        x_max = (  (x_max-x_min)//res +1 ) * res + x_min
        y_max = (  (y_max-y_min)//res +1 ) * res + y_min
        
        target_x_shape = int((x_max - x_min ) / res)
        target_y_shape = int((y_max - y_min ) / res)

        # print(target_x_shape, target_y_shape)
        # le query de téléchargement ne peut avoir + de 5000 pxl en taille de coté
        dl_suffix = []
        save_name = []
        if (target_x_shape < 5000) and (target_y_shape < 5000):
            dl_suffix.append( f"&BBOX={x_min},{y_min},{x_max},{y_max}&WIDTH={target_x_shape}&HEIGHT={target_y_shape}" )
            save_name.append( os.path.basename(save_path) )
        else:
            tile_on_x = math.ceil(target_x_shape / 5000)
            tile_on_y = math.ceil(target_y_shape / 5000)

            size_m_max = res * 5000  # size in meters per tile

            for i in range(tile_on_x):
                x_min_tile = x_min + i * size_m_max
                x_max_tile = min(x_min + (i + 1) * size_m_max, x_max)

                # compute tile width in pixels (5000 max, smaller at the edge)
                tile_width = min(5000, target_x_shape - i * 5000)

                for j in range(tile_on_y):
                    y_min_tile = y_min + j * size_m_max
                    y_max_tile = min(y_min + (j + 1) * size_m_max, y_max)

                    tile_height = min(5000, target_y_shape - j * 5000)

                    dl_suffix.append(
                        f"&BBOX={x_min_tile},{y_min_tile},{x_max_tile},{y_max_tile}&WIDTH={tile_width}&HEIGHT={tile_height}"
                    )
                    save_name.append(f"{i}_{j}_{os.path.basename(save_path)}")

        data_to_use = self.comb_to_use.currentText()

        if data_to_use == 'MNS': base_ign = self.base_mns_uri
        if data_to_use == 'MNT': base_ign = self.base_mnt_uri
        if data_to_use == 'MNH': base_ign = self.base_mnh_uri

        # print( dl_suffix)
        # print(save_name)

        # print( target_x_shape, target_y_shape)
        self.worker = DownloadWorker( base_ign, dl_suffix, save_name, save_path )
        
        self.worker.log_signal.connect(self.log_text.append)

        self.worker.start()

        # self.log_text.append( f'--------------------------')

        

from PyQt5.QtCore import QThread, pyqtSignal
import requests

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, base_ign, dl_suffix, save_name, save_path):
        super().__init__()
        self.base_ign = base_ign
        self.dl_suffix = dl_suffix
        self.save_name = save_name
        self.save_path = save_path

    def run(self):
        self.log_signal.emit('Début du téléchargement')

        saved_raster = []
        # dossier de DL
        dir_save = os.path.dirname(self.save_path)
        for i in range(len( self.dl_suffix)):
            full_uri = self.base_ign + self.dl_suffix[i] + f"&FILENAME={self.save_name[i]}"
            full_save_path = os.path.join( dir_save, self.save_name[i] )

            self.log_signal.emit(f">> téléchargement {i+1} / {len(self.dl_suffix)}")
            self.log_signal.emit(f"-->> Url {full_uri}")
            self.log_signal.emit(f"-->> Sauvegarde {full_save_path}")

            try:
                r = requests.get(full_uri, timeout=60)
                r.raise_for_status()

                with open(full_save_path, "wb") as f:
                    f.write(r.content)
                
                saved_raster.append( full_save_path )

            except requests.RequestException as e:
                print(f"Erreur {e}")
                continue
        
        if len(saved_raster) ==0:
            return
        elif len(saved_raster) ==1:
            QgsProject.instance().addMapLayer( QgsRasterLayer(saved_raster[0],os.path.basename(saved_raster[0]).replace('.tif','')) )
        else:
            # build a vrt in case of a lot of tiles
            self.log_signal.emit(f"Construction d'un vrt temporaire pour Qgis")
            vrt_process = processing.run("gdal:buildvirtualraster", 
                        {'INPUT':saved_raster,
                        'RESOLUTION':0,
                        'SEPARATE':False,
                        'PROJ_DIFFERENCE':False,
                        'ADD_ALPHA':False,
                        'ASSIGN_CRS':None,
                        'RESAMPLING':0,
                        'SRC_NODATA':'',
                        'EXTRA':'',
                        'OUTPUT': 'TEMPORARY_OUTPUT'})
            QgsProject.instance().addMapLayer( QgsRasterLayer(vrt_process['OUTPUT'],os.path.basename(self.save_path).replace('.tif','')) )
            

        