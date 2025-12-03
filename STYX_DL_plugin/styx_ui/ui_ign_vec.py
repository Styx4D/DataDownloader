from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QTextEdit
from PyQt5.QtCore import Qt
from owslib.wfs import WebFeatureService
from qgis.gui import    QgsExtentWidget
from qgis.core import  QgsCoordinateReferenceSystem

import urllib.request
from urllib.parse import quote
from io import BytesIO
import zipfile
from qgis.core import *

class Ui_IGN_vec_DL(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.setWindowTitle("BDD vecteur IGN")

        # lien wfs IGN
        self.wfs_url = "https://data.geopf.fr/wfs/ows?"

        # query data telechargeable
        wfs = WebFeatureService(url=self.wfs_url, version='2.0.0')
        self.items = list(wfs.contents)

        # uncheck par defaut
        self.checked_states = {item: Qt.CheckState.Unchecked for item in self.items}

        # Layout
        self.layout = QVBoxLayout(self)

        # Search bar
        self.add_line('Donnée à télécharger')
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.update_list)
        self.layout.addWidget(self.search_bar)

        # List widget (checkable items)
        self.list_widget = QListWidget(self)
        self.list_widget.setMinimumHeight(50)  
        self.list_widget.setMaximumHeight(100)  
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.layout.addWidget(self.list_widget)
        self.update_list()

        # extent
        self.extent_widget = QgsExtentWidget(self)
        self.extent_widget.setMapCanvas(self.iface.mapCanvas())
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
       
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
        self.save_path_button.clicked.connect(self.select_save_path)

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


    def add_line(self, label=None, default_data=None):
        row_layout = QHBoxLayout()
        if label is not None:
            label_q = QLabel(label)
            row_layout.addWidget(label_q)
        if default_data is not None:
            row_layout.addWidget(default_data)
        self.layout.addLayout(row_layout)

    def update_list(self):
        """Filter the list based on search input while preserving checked state."""
        search_text = self.search_bar.text().lower()
        self.list_widget.clear()

        for item_text in self.items:
            if search_text in item_text.lower():
                item = QListWidgetItem(item_text)
                # Preserve checked state
                item.setCheckState(self.checked_states.get(item_text, Qt.CheckState.Unchecked))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                self.list_widget.addItem(item)

        # Connect the itemChanged signal to track check/uncheck
        self.list_widget.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item: QListWidgetItem):
        """Track checked state changes."""
        self.checked_states[item.text()] = item.checkState()

    def get_selected_items(self):
        """Return a list of checked items."""
        return [item for item, state in self.checked_states.items() if state == Qt.CheckState.Checked]

    def print_selected(self):
        print("Selected items:", self.get_selected_items())
        
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
        
        extent = self.extent_widget.outputExtent()

        self.worker = DownloadWorker( self.wfs_url, self.get_selected_items(), extent, save_path)
        
        self.worker.log_signal.connect(self.log_text.append)

        self.worker.start()

        self.log_text.append( f'--------------------------')

        

from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import requests
import xml.etree.ElementTree as ET

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, wfs_link, names_to_dl, extent, save_path):
        super().__init__()
        self.wfs_link = wfs_link
        self.names_to_dl = names_to_dl
        self.extent = extent
        self.save_path = save_path

    def run(self):
        try:
            self.log_signal.emit('Début du téléchargement\n')

            for name in self.names_to_dl:
                self.log_signal.emit(f">> téléchargement de {name}\n")

                geom_name = self.get_wfs_geom_field(name)
                xmin, ymin, xmax, ymax = self.extent.xMinimum(), self.extent.yMinimum(), self.extent.xMaximum(), self.extent.yMaximum()
                wkt_poly = f"POLYGON(({xmin} {ymin},{xmax} {ymin},{xmax} {ymax},{xmin} {ymax},{xmin} {ymin}))"
                cql_filter = f"INTERSECTS({geom_name},SRID=4326;{wkt_poly})"
                cql_filter_encoded = quote(cql_filter)


                url = (
                    f"{self.wfs_link}"
                    f"service=WFS&version=2.0.0&request=GetFeature"
                    f"&typename={name}"
                    f"&srsname=EPSG:4326"
                    f"&outputFormat=SHAPE-ZIP"
                    f"&cql_filter={cql_filter_encoded}"
                )

                with urllib.request.urlopen(url) as response:
                    data = response.read()

                with BytesIO(data) as zipdata:
                    with zipfile.ZipFile(zipdata) as z:
                        z.extractall(self.save_path)

        except Exception:
            err = traceback.format_exc()
            self.log_signal.emit(f"[ERROR]\n{err}")
        self.log_signal.emit(" Done ! ")
    
    def get_wfs_geom_field(self, typename):
        
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "DescribeFeatureType",
            "typename": typename
        }
        r = requests.get(self.wfs_link[:-1], params=params)
        r.raise_for_status()

        root = ET.fromstring(r.text)
        ns = {"xsd": "http://www.w3.org/2001/XMLSchema"}
        geom_fields = []

        for elem in root.findall(".//xsd:element", ns):
            type_attr = elem.get("type", "")
            if "gml" in type_attr.lower():  # champ géométrique probable
                geom_fields.append(elem.get("name"))

        return geom_fields[0] if geom_fields else None
