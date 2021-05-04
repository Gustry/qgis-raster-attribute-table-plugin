# coding=utf-8
""""Test RAT classes

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

"""

__author__ = 'elpaso@itopen.it'
__date__ = '2021-04-27'
__copyright__ = 'Copyright 2021, ItOpen'


from osgeo import gdal
import os
import shutil
from unittest import TestCase, main
from qgis.PyQt.QtCore import QTemporaryDir, QVariant, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsRasterLayer
from rat_utils import get_rat, rat_classify
from rat_classes import RAT, RATField
from rat_constants import RAT_COLOR_HEADER_NAME


class TestRATClasses(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.qgs = QgsApplication([], False)
        cls.qgs.initQgis()

    @classmethod
    def tearDownClass(cls):

        cls.qgs.exitQgis()

    def tearDown(self):

        del(self.raster_layer)
        del(self.raster_layer_dbf)
        del(self.raster_layer_athematic)

    def setUp(self):

        self.tmp_dir = QTemporaryDir()
        self.tmp_path = os.path.join(self.tmp_dir.path(), 'data')

        shutil.copytree(os.path.join(os.path.dirname(
            __file__), 'data'), self.tmp_path)

        self.raster_layer = QgsRasterLayer(os.path.join(
            self.tmp_path, 'NBS_US5PSMBE_20200923_0_generalized_p.source_information.tiff'), 'rat_test', 'gdal')
        self.assertTrue(self.raster_layer.isValid())

        self.raster_layer_dbf = QgsRasterLayer(os.path.join(
            self.tmp_path, 'ExistingVegetationTypes_sample.img'), 'rat_test', 'gdal')
        self.assertTrue(self.raster_layer_dbf.isValid())

        self.raster_layer_athematic = QgsRasterLayer(os.path.join(
            self.tmp_path, '2x2_1_BAND_FLOAT.tif'), 'rat_test', 'gdal')
        self.assertTrue(self.raster_layer_athematic.isValid())

    def test_field_usages(self):

        rat = get_rat(self.raster_layer, 1)
        self.assertTrue(rat.isValid())
        self.assertEqual(rat.field_usages, {0, 1, 5})

    def test_insert_column(self):

        rat = get_rat(self.raster_layer, 1)
        self.assertTrue(rat.isValid())
        self.assertEqual(len(rat.keys), 16)
        self.assertEqual(len(rat.keys), len(rat.fields))

        # Not valid insertions
        field = RATField('f1', gdal.GFU_MinMax, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(4, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(0, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(1, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(100, field)[0])

        field = RATField('significant_features',
                         gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(4, field)[0])

        # Valid insertions

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertEqual(field.qgis_type, QVariant.Double)
        self.assertTrue(rat.insert_column(4, field)[0])
        self.assertIn('f1', rat.fields.keys())
        self.assertEqual(len(rat.data['f1']), len(rat.data['Value']))

        field = RATField('f2', gdal.GFU_Generic, gdal.GFT_Integer)
        self.assertEqual(field.qgis_type, QVariant.Int)
        self.assertTrue(rat.insert_column(2, field)[0])
        self.assertIn('f2', rat.fields.keys())
        self.assertEqual(len(rat.data['f2']), len(rat.data['Value']))
        self.assertEqual(rat.data['f2'][0], 0)

        field = RATField('f3', gdal.GFU_Generic, gdal.GFT_String)
        self.assertEqual(field.qgis_type, QVariant.String)
        self.assertTrue(rat.insert_column(len(rat.keys) - 1, field)[0])
        self.assertIn('f3', rat.fields.keys())
        self.assertEqual(len(rat.data['f3']), len(rat.data['Value']))
        self.assertEqual(rat.data['f3'][0], '')

    def test_remove_column(self):

        rat = get_rat(self.raster_layer, 1)
        self.assertTrue(rat.isValid())
        self.assertEqual(len(rat.keys), 16)
        self.assertEqual(len(rat.keys), len(rat.fields))

        # Invalid removals
        self.assertFalse(rat.remove_column('Value')[0])
        self.assertFalse(rat.remove_column('Count')[0])
        self.assertFalse(rat.remove_column('not found')[0])

        # Valid removals
        self.assertTrue(rat.remove_column('data_assessment')[0])
        self.assertEqual(len(rat.keys), 15)
        self.assertEqual(len(rat.keys), len(rat.fields))

    def test_insert_column_dbf(self):

        rat = get_rat(self.raster_layer_dbf, 1)
        self.assertTrue(rat.isValid())
        self.assertEqual(len(rat.keys), 17)
        # has color, so fields are one more than keys
        self.assertEqual(len(rat.keys), len(rat.fields) + 1)

        # Not valid insertions
        field = RATField('f1', gdal.GFU_MinMax, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(4, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(0, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(1, field)[0])

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(100, field)[0])

        field = RATField('SYSTMGRPNA',
                         gdal.GFU_Generic, gdal.GFT_Real)
        self.assertFalse(rat.insert_column(4, field)[0])

        # Valid insertions

        field = RATField('f1', gdal.GFU_Generic, gdal.GFT_Real)
        self.assertEqual(field.qgis_type, QVariant.Double)
        self.assertTrue(rat.insert_column(4, field)[0])
        self.assertIn('f1', rat.fields.keys())
        self.assertEqual(len(rat.data['f1']), len(rat.data['VALUE']))

        field = RATField('f2', gdal.GFU_Generic, gdal.GFT_Integer)
        self.assertEqual(field.qgis_type, QVariant.Int)
        self.assertTrue(rat.insert_column(2, field)[0])
        self.assertIn('f2', rat.fields.keys())
        self.assertEqual(len(rat.data['f2']), len(rat.data['VALUE']))
        self.assertEqual(rat.data['f2'][0], 0)

        field = RATField('f3', gdal.GFU_Generic, gdal.GFT_String)
        self.assertEqual(field.qgis_type, QVariant.String)
        self.assertTrue(rat.insert_column(len(rat.keys) - 1, field)[0])
        self.assertIn('f3', rat.fields.keys())
        self.assertEqual(len(rat.data['f3']), len(rat.data['VALUE']))
        self.assertEqual(rat.data['f3'][0], '')

        field = RATField('R', gdal.GFU_Red, gdal.GFT_Integer)
        self.assertFalse(rat.insert_column(len(rat.keys) - 1, field)[0])

    def test_remove_column_dbf(self):

        rat = get_rat(self.raster_layer_dbf, 1)
        self.assertTrue(rat.isValid())
        self.assertEqual(len(rat.keys), 17)
        self.assertEqual(len(rat.keys), len(rat.fields) + 1)

        # Invalid removals
        self.assertFalse(rat.remove_column('VALUE')[0])
        self.assertFalse(rat.remove_column('COUNT')[0])
        self.assertFalse(rat.remove_column('not found')[0])

        # Valid removals
        self.assertTrue(rat.remove_column('SYSTMGRPNA')[0])
        self.assertEqual(len(rat.keys), 16)
        self.assertEqual(len(rat.keys), len(rat.fields) + 1)

    def test_qgis_features(self):

        rat = get_rat(self.raster_layer_dbf, 1)
        features = rat.qgis_features()
        self.assertEqual(len(features), 59)

        rat = get_rat(self.raster_layer, 1)
        features = rat.qgis_features()
        self.assertEqual(len(features), 27)

    def test_get_set_color(self):

        rat = get_rat(self.raster_layer_dbf, 1)
        color = rat.get_color(0)
        self.assertTrue(color.isValid())

        # Invalid
        self.assertFalse(rat.get_color(-1).isValid())
        self.assertFalse(rat.get_color(100).isValid())

        # Setter
        self.assertTrue(rat.set_color(1, QColor(10, 20, 30, 120)))
        self.assertEqual(rat.get_color(1), QColor(10, 20, 30, 120))

    def test_field_name(self):

        rat = get_rat(self.raster_layer_dbf, 1)

        usages = []
        for field in rat.fields.values():
            if field.usage not in usages:
                usages.append(field.usage)
                self.assertEqual(rat.field_name(field.usage), field.name)

        self.assertEqual(rat.field_name(gdal.GFU_AlphaMax), '')
        self.assertEqual(rat.field_name(gdal.GFU_RedMax), '')
        self.assertEqual(rat.field_name(gdal.GFU_RedMin), '')

    def test_update_color_from_raster(self):

        rat = get_rat(self.raster_layer_dbf, 1)
        self.assertTrue(rat.has_color)
        rat_classify(self.raster_layer_dbf, 1, rat, 'EVT_NAME')

        color_map = {
            klass.value: klass.color for klass in self.raster_layer_dbf.renderer().classes()}

        # Remove color
        self.assertTrue(rat.remove_color_fields())
        self.assertFalse(rat.has_color)

        # Add color
        result, error_message = rat.insert_color_fields(len(rat.keys)-1)
        self.assertTrue(result, error_message)
        self.assertTrue(rat.has_color)

        for color in rat.data[RAT_COLOR_HEADER_NAME]:
            self.assertEqual(color, QColor(Qt.black))

        # Update color from raster
        self.assertTrue(rat.update_colors_from_raster(self.raster_layer_dbf))

        value_column = rat.value_columns[0]
        self.assertEqual(value_column, rat.field_name(gdal.GFU_MinMax))

        for row_index in range(len(rat.data[RAT_COLOR_HEADER_NAME])):
            self.assertEqual(rat.data[RAT_COLOR_HEADER_NAME][row_index],
                             color_map[rat.data[value_column][row_index]])

    def test_update_color_from_raster_athematic(self):

        rat = get_rat(self.raster_layer_athematic, 1)
        self.assertTrue(rat.has_color)
        rat_classify(self.raster_layer_athematic, 1, rat, 'Class')

        shader = self.raster_layer_athematic.renderer().shader()
        colorRampShaderFcn = shader.rasterShaderFunction()
        classes = classes = colorRampShaderFcn.colorRampItemList()

        color_map = {klass.value: klass.color for klass in classes}

        # Remove color
        self.assertTrue(rat.remove_color_fields())
        self.assertFalse(rat.has_color)

        # Add color
        result, error_message = rat.insert_color_fields(len(rat.keys)-1)
        self.assertTrue(result, error_message)
        self.assertTrue(rat.has_color)

        for color in rat.data[RAT_COLOR_HEADER_NAME]:
            self.assertEqual(color, QColor(Qt.black))

        # Update color from raster
        self.assertTrue(rat.update_colors_from_raster(
            self.raster_layer_athematic))

        value_column = rat.value_columns[1]
        self.assertEqual(value_column, rat.field_name(gdal.GFU_Max))

        for row_index in range(len(rat.data[RAT_COLOR_HEADER_NAME])):
            self.assertEqual(rat.data[RAT_COLOR_HEADER_NAME][row_index],
                             color_map[rat.data[value_column][row_index]])

    def test_add_remove_row(self):

        def _test(raster_layer):

            rat = get_rat(raster_layer, 1)
            value_column = rat.value_columns[0]
            self.assertEqual(value_column, rat.field_name(gdal.GFU_MinMax))

            self.assertNotEqual(rat.data[value_column][-1], 0)
            row_count = len(rat.data[value_column])

            result, error_message = rat.insert_row(0)
            self.assertTrue(result)
            self.assertEqual(len(rat.data[value_column]), row_count + 1)
            self.assertEqual(rat.data[value_column][0], 0)

            result, error_message = rat.remove_row(0)
            self.assertTrue(result)
            self.assertEqual(len(rat.data[value_column]), row_count)
            self.assertNotEqual(rat.data[value_column][0], 0)

            last = len(rat.data[value_column])
            result, error_message = rat.insert_row(last)
            self.assertTrue(result)
            self.assertEqual(len(rat.data[value_column]), row_count + 1)
            self.assertEqual(rat.data[value_column][last], 0)

            result, error_message = rat.remove_row(last)
            self.assertTrue(result)
            self.assertEqual(len(rat.data[value_column]), row_count)
            self.assertNotEqual(rat.data[value_column][last - 1], 0)

            # Invalid ranges
            last = len(rat.data[value_column])
            self.assertFalse(rat.insert_row(-1)[0])
            self.assertFalse(rat.insert_row(last + 1)[0])
            self.assertFalse(rat.remove_row(-1)[0])
            self.assertFalse(rat.remove_row(last)[0])

        _test(self.raster_layer_dbf)
        _test(self.raster_layer)

    def test_edit_rat(self):

        raster_layer = QgsRasterLayer(os.path.join(
            self.tmp_path, '2x2_2_BANDS_INT16.tif'), 'rat_test', 'gdal')
        self.assertTrue(raster_layer.isValid())

        band = 1

        rat = get_rat(raster_layer, band)
        self.assertTrue(rat.isValid())

        self.assertEqual(rat.data['Red'], [0, 100, 200])
        rat.data['Red'] = [111, 222, 123]
        rat.save(band)

        rat = get_rat(raster_layer, band)
        self.assertTrue(rat.isValid())
        self.assertEqual(rat.data['Red'], [111, 222, 123])


if __name__ == '__main__':
    main()
