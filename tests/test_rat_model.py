# coding=utf-8
""""RAT model tests

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

"""

__author__ = 'elpaso@itopen.it'
__date__ = '2021-04-27'
__copyright__ = 'Copyright 2021, ItOpen'


import os
from osgeo import gdal
import shutil
from unittest import TestCase, main
from qgis.PyQt.QtCore import QTemporaryDir
from qgis.core import QgsRasterLayer
from rat_utils import get_rat
from rat_model import RATModel
from rat_classes import RATField

class TestRATModel(TestCase):

    def setUp(self):

        self.tmp_dir = QTemporaryDir()
        self.tmp_path = os.path.join(self.tmp_dir.path(), 'data')

        shutil.copytree(os.path.join(os.path.dirname(
            __file__), 'data'), self.tmp_path)

        self.raster_layer = QgsRasterLayer(os.path.join(
            self.tmp_path, 'NBS_US5PSMBE_20200923_0_generalized_p.source_information.tiff'), 'rat_test', 'gdal')
        self.assertTrue(self.raster_layer.isValid())

    def test_insert_column(self):

        rat = get_rat(self.raster_layer, 1)
        self.assertTrue(rat.isValid())

        model = RATModel(rat)
        column_count = model.columnCount(model.index(0,0))
        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_String)
        self.assertTrue(model.insert_column(3, field)[0])
        self.assertEqual(model.columnCount(
            model.index(0, 0)), column_count + 1)

        # Error
        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_String)
        self.assertFalse(model.insert_column(3, field)[0])
        self.assertEqual(model.columnCount(
            model.index(0, 0)), column_count + 1)

    def test_remove_column(self):

        rat = get_rat(self.raster_layer, 1)
        self.assertTrue(rat.isValid())

        model = RATModel(rat)
        column_count = model.columnCount(model.index(0, 0))
        self.assertFalse(model.remove_column(0)[0])
        self.assertFalse(model.remove_column(1)[0])
        self.assertTrue(model.remove_column(2)[0])
        self.assertEqual(model.columnCount(
            model.index(0, 0)), column_count - 1)

    def test_add_color(self):

        pass

    def test_remove_color(self):

        pass






