from qgis.PyQt.QtWidgets import QAction
from PyQt5.QtWidgets import QAction, QMenu, QToolButton, QToolBar
from qgis.PyQt.QtGui import QIcon
import os

from .styx_ui.ui_sentinel_DL import Ui_sent_DL
from .styx_ui.ui_ign_vec import Ui_IGN_vec_DL
from .styx_ui.ui_geol_DL import Ui_geol_DL
from .styx_ui.ui_lidar_ign import Ui_IGN_DEM_DL

class styx4d_DL_plugin:
    def __init__(self, iface):
        self.iface = iface


    def initGui(self):
        """ logo (mettre celui en RGBA à l'occas) """
        icon_path = os.path.join( os.path.dirname(os.path.realpath(__file__)), "styx_ico.png")
        self.logo_action = QAction(QIcon(icon_path), 'Logo', self.iface.mainWindow())
        
        """ MENU DL """
        self.sent_dl_action = QAction('Sentinel2', self.iface.mainWindow())
        self.sent_dl_action.triggered.connect(self.run_sent_dl)

        self.ign_dl_action = QAction('IGN vecteur', self.iface.mainWindow())
        self.ign_dl_action.triggered.connect(self.run_ign_dl)

        self.geol_dl_action = QAction('Geol 1/50000', self.iface.mainWindow())
        self.geol_dl_action.triggered.connect(self.run_geol_dl)

        self.lidar_ign_action = QAction('lidar - IGN', self.iface.mainWindow())
        self.lidar_ign_action.triggered.connect(self.run_lidar_ign)

        self.DL_menu = QMenu('Téléchargement', self.iface.mainWindow())
        self.DL_menu.addAction(self.sent_dl_action)
        self.DL_menu.addAction(self.ign_dl_action)
        self.DL_menu.addAction(self.geol_dl_action)
        self.DL_menu.addAction(self.lidar_ign_action)

        self.DL_button = QToolButton()
        self.DL_button.setText('Téléchargement')
        self.DL_button.setMenu(self.DL_menu)
        self.DL_button.setPopupMode(QToolButton.InstantPopup)

        """ ADD TO TOOLBAR """
        # Create a toolbar and add the tool button
        self.toolbar = QToolBar(self.iface.mainWindow())
        self.toolbar.addAction(self.logo_action)
        self.toolbar.addWidget(self.DL_button)

        # Add the toolbar to the main interface
        self.iface.addToolBar(self.toolbar)
        
    def unload(self):
        # self.iface.removeToolBar(self.toolbar)
        parent = self.toolbar.parentWidget()
        parent.removeToolBar(self.toolbar)

    def run_sent_dl(self):
        self.dialog_dl = Ui_sent_DL(self.iface)
        self.dialog_dl.show()  # Display the dialog
        self.dialog_dl.exec_()  # Open as a modal dialog

    def run_geol_dl(self):
        self.dialog_dl = Ui_geol_DL(self.iface)
        self.dialog_dl.show()  
        self.dialog_dl.exec_()  

    def run_lidar_ign(self):
        self.dialog_dl = Ui_IGN_DEM_DL(self.iface)
        self.dialog_dl.show()  
        self.dialog_dl.exec_()  

    def run_ign_dl(self):
        self.dialog_ign_vec = Ui_IGN_vec_DL(self.iface)
        self.dialog_ign_vec.show()  
        self.dialog_ign_vec.exec_()

        

