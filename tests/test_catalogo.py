"""Pruebas mínimas del catálogo y sus características científicas.
Ejecutar: python -m unittest discover -s tests -v
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts'/'preparar_catalogo.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)

class TestCatalogo(unittest.TestCase):
    def raster(self,path,arr,crs='EPSG:32628',nodata=-9999):
        with rasterio.open(path,'w',driver='GTiff',width=arr.shape[1],height=arr.shape[0],count=1,
                           dtype='float32',crs=crs,nodata=nodata,
                           transform=from_origin(0,5000,5000/arr.shape[1],5000/arr.shape[0])) as ds:
            ds.write(arr.astype('float32'),1)

    def test_plano(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'flat.tif';self.raster(p,np.full((30,30),120.))
            r=pipeline.compute_features(p)
            self.assertAlmostEqual(r['metrics']['pendiente_media_deg'],0,places=6)
            self.assertAlmostEqual(r['metrics']['razon_area_3d2d'],1,places=6)
            self.assertAlmostEqual(r['metrics']['tri_normalizado'],0,places=6)

    def test_pendiente_constante(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'slope.tif'
            grid=np.tile(np.arange(30,dtype=float)*2,(30,1));self.raster(p,grid)
            r=pipeline.compute_features(p)
            self.assertGreater(r['metrics']['pendiente_media_deg'],0.3)
            self.assertGreater(r['metrics']['razon_area_3d2d'],1)
            self.assertEqual(r['size'],[30,30])

    def test_dem_sin_crs_rechazado(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'nocrs.tif';self.raster(p,np.ones((10,10)),crs=None)
            with self.assertRaises(ValueError):pipeline.compute_features(p)

    def test_catalogo_tiene_contratos(self):
        d=json.loads((ROOT/'data'/'catalog.json').read_text(encoding='utf8'))
        self.assertEqual(len(d['items']),33)
        self.assertEqual(len({v['id'] for v in d['items']}),33)
        self.assertTrue(any(r['body']=='Marte' for r in d['items']))
        self.assertTrue(any(r['body']=='Luna' for r in d['items']))
        avail=[v for v in d['items'] if v['status']=='disponible']
        self.assertGreaterEqual(len(avail),5)
        for v in avail:
            self.assertEqual(set(v['assets']),set(pipeline.SIX))
            for f in v['assets'].values():self.assertTrue((ROOT/f).is_file(),f)
            self.assertEqual(len(v['metrics']),7)

    def test_plotly_referencia_relativa(self):
        d=json.loads((ROOT/'data'/'catalog.json').read_text(encoding='utf8'))
        js=ROOT/'data'/'regions'/'plotly.min.js'
        self.assertTrue(js.is_file())
        for r in d['items']:
            if r['status']=='disponible':
                html=(ROOT/r['assets']['Terreno_3D.html']).read_text(encoding='utf8')
                self.assertIn('../plotly.min.js',html)

if __name__=='__main__':unittest.main()
