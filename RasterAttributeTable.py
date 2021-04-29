# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : RasterAttributeTable
Description          : RasterAttributeTable
Date                 : 12/Oct/2020
copyright            : (C) 2020 by ItOpen
email                : elpaso@itopen.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from functools import partial

from osgeo import gdal
from qgis.core import (QgsApplication, QgsMapLayer, QgsMapLayerType,
                       QgsMessageLog, QgsProject, Qgis)
from qgis.PyQt.QtCore import QCoreApplication, Qt, pyqtSlot, QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QPushButton

from .dialogs.RasterAttributeTableDialog import RasterAttributeTableDialog
from .dialogs.CreateRasterAttributeTableDialog import CreateRasterAttributeTableDialog
from .rat_utils import rat_log, has_rat, can_create_rat, deduplicate_legend_entries, homogenize_colors
from .rat_constants import RAT_CUSTOM_PROPERTY_CLASSIFICATION_CRITERIA


class RasterAttributeTable(QObject):

    def __init__(self, iface):

        super().__init__()
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.open_rat_action = QAction(
            QgsApplication.getThemeIcon("/mActionOpenTable.svg"), QCoreApplication.translate("RAT", "&Open Attribute Table"))
        self.create_rat_action = QAction(
            QgsApplication.getThemeIcon("/mActionAddTable.svg"), QCoreApplication.translate("RAT", "&New Attribute Table"))
        rat_log("Init completed")

    def initGui(self):

        QgsProject.instance().layerWasAdded.connect(self.updateRatActions)
        QgsProject.instance().layerWasAdded.connect(self.connectRendererChanged)
        QgsProject.instance().layerWasAdded.connect(self.notifyUserOnRatAvailable)

        for layer in list(QgsProject.instance().mapLayers().values()):
            self.connectRendererChanged(layer)
            self.updateRatActions(layer)

        self.open_rat_action.triggered.connect(self.showAttributeTable)
        self.create_rat_action.triggered.connect(self.showCreateRatDialog)

        rat_log("GUI loaded")

    def unload(self):

        self.iface.removeCustomActionForLayerType(self.open_rat_action)
        self.iface.removeCustomActionForLayerType(self.create_rat_action)
        rat_log("GUI unloaded")

    @pyqtSlot(QgsMapLayer)
    def notifyUserOnRatAvailable(self, layer):

        if layer and layer.type() == QgsMapLayerType.RasterLayer:
            if has_rat(layer):
                if not layer.customProperty(RAT_CUSTOM_PROPERTY_CLASSIFICATION_CRITERIA):
                    widget = self.iface.messageBar().createMessage(
                        QCoreApplication.translate("RAT", "RAT Available"),
                        QCoreApplication.translate("RAT", "Raster <b>%s</b> has an associated attribute table." % layer.name()))
                    button = QPushButton(widget)
                    button.setText("Open Raster Attribute Table")
                    button.pressed.connect(
                        partial(self.showAttributeTable, layer=layer))
                    widget.layout().addWidget(button)
                    self.iface.messageBar().pushWidget(widget, Qgis.Info)

    @pyqtSlot(QgsMapLayer)
    def updateRatActions(self, *args):

        self.iface.removeCustomActionForLayerType(self.open_rat_action)
        self.iface.removeCustomActionForLayerType(self.create_rat_action)

        self.iface.addCustomActionForLayerType(self.open_rat_action,
                                               None, QgsMapLayerType.RasterLayer, allLayers=False)
        self.iface.addCustomActionForLayerType(self.create_rat_action,
                                               None, QgsMapLayerType.RasterLayer, allLayers=False)

        for layer in QgsProject.instance().mapLayers().values():
            if layer and layer.type() == QgsMapLayerType.RasterLayer:
                if has_rat(layer):
                    self.iface.addCustomActionForLayer(
                        self.open_rat_action, layer)
                    rat_log("Open RAT action added for: %s" %
                            layer.name())
                else:
                    criteria = layer.customProperty(
                        RAT_CUSTOM_PROPERTY_CLASSIFICATION_CRITERIA, False)
                    if criteria:
                        layer.removeCustomProperty(
                            RAT_CUSTOM_PROPERTY_CLASSIFICATION_CRITERIA)
                        rat_log(
                            'Layer %s has been adopted but its RAT got lost.' % layer.name())

                    if can_create_rat(layer):
                        self.iface.addCustomActionForLayer(
                            self.create_rat_action, layer)
                        rat_log("Create RAT action added for: %s" %
                                layer.name())

    @pyqtSlot(QgsMapLayer)
    def connectRendererChanged(self, layer):
        """Makes sure the actions are updated if the renderer changes"""

        if layer and layer.type() == QgsMapLayerType.RasterLayer:
            layer.rendererChanged.connect(
                self.rendererChanged, Qt.UniqueConnection)

    @pyqtSlot()
    def rendererChanged(self):

        raster_layer = self.sender()
        self.updateRatActions(raster_layer)
        criteria = raster_layer.customProperty(
            RAT_CUSTOM_PROPERTY_CLASSIFICATION_CRITERIA, False)
        if criteria and has_rat(raster_layer):
            raster_layer.rendererChanged.disconnect(self.rendererChanged)
            if homogenize_colors(self.iface, raster_layer):
                self.iface.messageBar().pushMessage(
                    QCoreApplication.translate('RAT', "Style reset"),
                    QCoreApplication.translate('RAT', "The layer style is managed by the RAT plugin: colors have been homogenized to match the first class in the classification group."), level=Qgis.Info)
            raster_layer.rendererChanged.connect(
                self.rendererChanged, Qt.UniqueConnection)
            deduplicate_legend_entries(self.iface, raster_layer, criteria)

    def showCreateRatDialog(self, checked=False, layer=None):

        if layer is None:
            layer = self.iface.activeLayer()

        self.create_dlg = CreateRasterAttributeTableDialog(layer, self.iface)
        self.create_dlg.ratCreated.connect(self.notifyUserOnRatAvailable)
        self.create_dlg.ratCreated.connect(self.updateRatActions)
        self.create_dlg.exec_()

    def showAttributeTable(self, checked=False, layer=None):

        if layer is None:
            layer = self.iface.activeLayer()
        self.dlg = RasterAttributeTableDialog(layer, self.iface)
        self.dlg.show()
