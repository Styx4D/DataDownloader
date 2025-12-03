from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QFileDialog, QMenuBar, QMenu, QAction, QCheckBox, QDoubleSpinBox,
    QStyledItemDelegate, qApp, QSpinBox, QDateEdit, QTextEdit, QMessageBox
    
)
from PyQt5.QtGui import QFontMetrics, QStandardItem, QPalette
from PyQt5.QtCore import QEvent, QDate

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import os
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsProjectionSelectionWidget, QgsExtentWidget
from qgis.core import QgsMapLayerProxyModel, QgsCoordinateReferenceSystem

from qgis.core import QgsProcessingParameterExtent
from qgis.gui import QgsExtentGroupBox

from ..styx_utils.copernicus_api import  get_data_link, download_archive_with_try_nodes, download_archive_with_try


from PyQt5.QtWidgets import QDialog, QVBoxLayout
from qgis.core import (
    QgsProcessingParameterExtent,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsRectangle
)
from qgis.gui import QgsExtentGroupBox

METADATA_FILES = [
    'INSPIRE.xml',
    'manifest.safe',
    'MTD_MSIL2A.xml',
    'MTD_TL.xml',
    'FORMAT_CORRECTNESS.xml',
    'GENERAL_QUALITY.xml',
    'GEOMETRIC_QUALITY.xml',
    'L2A_QUALITY.xml',
    'SENSOR_QUALITY.xml'
]

MSK_FILES = [
    'MSK_CLASSI_B00.jp2',
    'MSK_CLDPRB_20m.jp2',
    'MSK_CLDPRB_60m.jp2',
    'MSK_DETFOO_B01.jp2',
    'MSK_DETFOO_B02.jp2',
    'MSK_DETFOO_B03.jp2',
    'MSK_DETFOO_B04.jp2',
    'MSK_DETFOO_B05.jp2',
    'MSK_DETFOO_B06.jp2',
    'MSK_DETFOO_B07.jp2',
    'MSK_DETFOO_B08.jp2',
    'MSK_DETFOO_B09.jp2',
    'MSK_DETFOO_B10.jp2',
    'MSK_DETFOO_B11.jp2',
    'MSK_DETFOO_B12.jp2',
    'MSK_DETFOO_B8A.jp2',
    'MSK_QUALIT_B01.jp2',
    'MSK_QUALIT_B02.jp2',
    'MSK_QUALIT_B03.jp2',
    'MSK_QUALIT_B04.jp2',
    'MSK_QUALIT_B05.jp2',
    'MSK_QUALIT_B06.jp2',
    'MSK_QUALIT_B07.jp2',
    'MSK_QUALIT_B08.jp2',
    'MSK_QUALIT_B09.jp2',
    'MSK_QUALIT_B10.jp2',
    'MSK_QUALIT_B11.jp2',
    'MSK_QUALIT_B12.jp2',
    'MSK_QUALIT_B8A.jp2',
    'MSK_SNWPRB_20m.jp2',
    'MSK_SNWPRB_60m.jp2'
]

BAND10_FILES = [
    'AOT_10m.jp2',
    'B02_10m.jp2',
    'B03_10m.jp2',
    'B04_10m.jp2',
    'B08_10m.jp2',
    'TCI_10m.jp2',
    'WVP_10m.jp2'
]

BAND20_FILES = [
    'AOT_20m.jp2',
    'B01_20m.jp2',
    'B02_20m.jp2',
    'B03_20m.jp2',
    'B04_20m.jp2',
    'B05_20m.jp2',
    'B06_20m.jp2',
    'B07_20m.jp2',
    'B11_20m.jp2',
    'B12_20m.jp2',
    'B8A_20m.jp2',
    'SCL_20m.jp2',
    'TCI_20m.jp2',
    'WVP_20m.jp2'
]

BAND60_FILES = [
    'AOT_60m.jp2',
    'B01_60m.jp2',
    'B02_60m.jp2',
    'B03_60m.jp2',
    'B04_60m.jp2',
    'B05_60m.jp2',
    'B06_60m.jp2',
    'B07_60m.jp2',
    'B09_60m.jp2',
    'B11_60m.jp2',
    'B12_60m.jp2',
    'B8A_60m.jp2',
    'SCL_60m.jp2',
    'TCI_60m.jp2',
    'WVP_60m.jp2'
]


class Ui_sent_DL(QDialog):
    def __init__(self, iface ):
        super().__init__(iface.mainWindow())
        self.iface = iface

        

        self.setWindowTitle('Téléchargement dalles Sentinel-2')
        self.layout = QVBoxLayout()

        self.add_line( '>>> Identifiant de connexion')
        self.add_line( '> A créer sur https://dataspace.copernicus.eu/')
        
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.add_line( 'Nom de compte :', self.username )
        self.add_line( 'Mot de passe :', self.password )

        self.add_line( '' )

        self.add_line( '>>> Critère de recherche' )
        # nom de la couche
        self.sent_name = QLineEdit()
        self.add_line( 'Nom', self.sent_name )

        # couv nuageuse
        self.cloud_cover = QSpinBox()
        self.cloud_cover.setMinimum(0)
        self.cloud_cover.setMaximum(100)   
        self.cloud_cover.setValue(90)
        self.add_line( 'Couverture nuageuse max', self.cloud_cover )
        
        # date
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))  # par défaut, 1 mois avant

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())  # par défaut, aujourd’hui

        self.add_line('Date de début', self.start_date)
        self.add_line('Date de fin', self.end_date)

        # extensions
        self.extent_widget = QgsExtentWidget(self)
        self.extent_widget.setMapCanvas(self.iface.mapCanvas())
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        # 

        # set à 0 par defaut (=pas dextent)
        default_extent = iface.mapCanvas().extent()
        self.extent_widget.setOriginalExtent( default_extent, iface.mapCanvas().mapSettings().destinationCrs() )
        self.extent_widget.setOutputCrs( target_crs )

        # for le in self.extent_widget.findChildren(QLineEdit):
        #     le.clear()

        self.add_line('Extent', self.extent_widget)

        # combobox à DL
        self.combo_metadata = CheckableComboBox()
        self.combo_msk = CheckableComboBox()
        self.combo_band10 = CheckableComboBox()
        self.combo_band20 = CheckableComboBox()
        self.combo_band60 = CheckableComboBox()

        self.combo_metadata.addItems(METADATA_FILES)
        self.combo_msk.addItems(MSK_FILES)
        self.combo_band10.addItems(BAND10_FILES)
        self.combo_band20.addItems(BAND20_FILES)
        self.combo_band60.addItems(BAND60_FILES)

        self.combo_metadata_label = QLabel('métadonnées')
        self.combo_msk_label = QLabel('mask')
        self.combo_band10_label = QLabel('bandes 10m')
        self.combo_band20_label = QLabel('bandes 20m')
        self.combo_band60_label = QLabel('bandes 60m')

        self.widgets_dl_list = [ self.combo_metadata, self.combo_msk, self.combo_band10, self.combo_band20, self.combo_band60 ]
        self.widgets_dl_list += [ self.combo_metadata_label, self.combo_msk_label, self.combo_band10_label, self.combo_band20_label, self.combo_band60_label ]        

        row_layout = QHBoxLayout()
        couple_lab_comb = [
            [self.combo_metadata_label, self.combo_metadata],
            [self.combo_msk_label, self.combo_msk],
            [self.combo_band10_label, self.combo_band10],
            [self.combo_band20_label, self.combo_band20],
            [self.combo_band60_label, self.combo_band60]
        ]
        for lab_comb in couple_lab_comb:
            lab, comb = lab_comb
            col_layout = QVBoxLayout()
            col_layout.addWidget(lab)
            col_layout.addWidget(comb)
            row_layout.addLayout(col_layout)

        # a DL
        self.add_line( '' )
        self.add_line( '>>> Données à télécharger' )
        self.combo_DL = QComboBox()
        self.combo_DL.addItems(["Tout", "Selection de couches"])
        self.combo_DL.currentIndexChanged.connect( self.update_layout )
        self.add_line('Selection', self.combo_DL)

        # ajout de la selection a dl dans le layout
        self.layout.addLayout(row_layout)
        self.update_layout()
        
        self.add_save_option()

        self.add_line( '' )
        self.add_line( '>>> Log' )
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)


        self.create_footer_buttons()

        self.setLayout(self.layout)
        self.resize(400, 150)
        
    def add_line(self, label=None, default_data=None):
        row_layout = QHBoxLayout()
        if label is not None:
            label_q = QLabel(label)
            row_layout.addWidget(label_q)
        if default_data is not None:
            row_layout.addWidget(default_data)
        self.layout.addLayout(row_layout)

    def update_layout(self, *args):
        if self.combo_DL.currentText() == 'Tout':
            should_show = False
        else:
            should_show = True

        for widgets_dl in self.widgets_dl_list:
            widgets_dl.setVisible(should_show)

    def add_save_option(self):
        # Path selection button and line edit
        save_layout = QVBoxLayout()

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText('[ Temporary File ]')
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

    def Qdate_to_list( self, Qdate_data ):
        Qdate_data = Qdate_data.date()
        return [ Qdate_data.year(), Qdate_data.month(), Qdate_data.day() ]
    
    def on_ok_button_clicked(self):
        # self.log_text.clear()

        save_path = self.save_path_edit.text()
        if not save_path:
            QMessageBox.warning(self, "Nope !", "Chemin de sauvegarde manquant")
            return


        username = self.username.text()
        password = self.password.text()

        if  (len(username) == 0) or (len(password)==0):
            QMessageBox.warning(self, "Nope !", "Identifiant manquant")
            return

        sent_name = self.sent_name.text()
        cloud_cover = self.cloud_cover.value()
        start_date = self.Qdate_to_list( self.start_date )
        end_date = self.Qdate_to_list( self.end_date )
        extent = self.extent_widget.outputExtent()

        # print( extent.toString() )
        if extent.toString() != 'Null':
            extent = [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum() ]
        else:
            extent = None

        dl_method = self.combo_DL.currentText()

        if dl_method =='Tout':
            layer_to_DL = 'all'
        else:
            layer_to_DL = self.combo_metadata.currentData()
            layer_to_DL += self.combo_msk.currentData()
            layer_to_DL += self.combo_band10.currentData()
            layer_to_DL += self.combo_band20.currentData()
            layer_to_DL += self.combo_band60.currentData()


        self.worker = DownloadWorker(username, password, sent_name, cloud_cover,
                        start_date, end_date, extent, layer_to_DL, save_path)
        
        self.worker.log_signal.connect(self.log_text.append)

        def on_finished(success, failed):
            self.log_text.append(f'Fin du téléchargement : {len(success)} success ; {len(failed)} fails')
            if failed:
                self.log_text.append('Erreur sur :')
                for d in failed:
                    if isinstance(d, dict):
                        self.log_text.append(f'  > {d["Name"]}')
                    else:
                        self.log_text.append(f'  > {d[0]} : {d[1]}')

        self.worker.finished_signal.connect(on_finished)
        self.worker.start()

        self.log_text.append( f'--------------------------')

        
from PyQt5.QtCore import QThread, pyqtSignal
import traceback

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list, list)  # success, failed

    def __init__(self, username, password, sent_name, cloud_cover, start_date, end_date, extent, layer_to_DL, save_path):
        super().__init__()
        self.username = username
        self.password = password
        self.sent_name = sent_name
        self.cloud_cover = cloud_cover
        self.start_date = start_date
        self.end_date = end_date
        self.extent = extent
        self.layer_to_DL = layer_to_DL
        self.save_path = save_path

    def run(self):
        try:
            self.log_signal.emit('Chargement des données disponible')
            keycloak_manager, all_data = get_data_link(
                self.username, self.password, self.sent_name,
                self.cloud_cover, self.start_date, self.end_date,
                self.extent, self.layer_to_DL
            )
            self.log_signal.emit(f'>> {len(all_data)} images trouvées')
            self.log_signal.emit('Début du téléchargement')

            if self.layer_to_DL == 'all':
                zip_paths, data_failed = download_archive_with_try(
                    keycloak_manager, all_data, self.save_path
                )
                self.finished_signal.emit(zip_paths, data_failed)
            else:
                data_ok, data_failed = download_archive_with_try_nodes(
                    keycloak_manager, all_data, self.save_path, self.layer_to_DL
                )
                self.finished_signal.emit(data_ok, data_failed)

        except Exception:
            err = traceback.format_exc()
            self.log_signal.emit(f"[ERROR]\n{err}")




class CheckableComboBox(QComboBox):

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        palette = qApp.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                texts.append(self.model().item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def addItem(self, text, data=None):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res