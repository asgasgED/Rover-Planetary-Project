"""Offline tests with five actual 5 km DEMs bundled with the application."""
from pathlib import Path
import os
import unittest
from unittest.mock import patch
import sys
import types
from fastapi.testclient import TestClient
from backend.api import app
from backend.analysis_engine import read_dem,features

ROOT=Path(__file__).resolve().parent.parent

class TestScientificBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)

    def test_public_assets_and_secret_inaccessible(self):
        for route in ('/','/index.html','/src/app.js','/src/v3_palette.css','/data/catalog.json'):
            self.assertEqual(self.client.get(route).status_code,200,route)
        for route in ('/.env','/backend/api.py','/backend/team_originals/graficos_terrarover.py',
                      '/datos_para_importar/entrega_5km/','/.gitignore'):
            self.assertEqual(self.client.get(route).status_code,404,route)

    def test_statistical_comparison_real_earth_moon(self):
        resp=self.client.post('/api/analyze',json={'a':'Timanfaya_ASTER','b':'Mare_Tranquillitatis_SLDEM'})
        self.assertEqual(resp.status_code,200,resp.text)
        a=resp.json()
        self.assertEqual(len(a['feature_comparison']),7)
        self.assertIsNone(a['pixelwise_difference'])
        self.assertFalse(a['fine_scale_comparison_permitted'])
        self.assertEqual(a['regions']['a_id'],'Timanfaya_ASTER')
        self.assertTrue(0<=a['normalized_elevation_wasserstein']<=1)
        self.assertEqual(len(a['interpretive_notes']),5)

    def test_mola_regional_only(self):
        r=self.client.post('/api/analyze',json={'a':'La_Joya_NASADEM','b':'Jezero_MOLA'})
        self.assertEqual(r.status_code,200,r.text)
        a=r.json();self.assertFalse(a['fine_scale_comparison_permitted'])
        self.assertTrue(any('native resolutions' in w.lower() for w in a['warnings']))
        self.assertIsNone(a['pixelwise_difference'])

    def test_unknown_missing_identical_and_attack(self):
        for req,code in [({'a':'Timanfaya_ASTER','b':'Timanfaya_ASTER'},400),
                         ({'a':'Timanfaya_ASTER','b':'Gale_Crater_MOLA'},409),
                         ({'a':'../../.env','b':'Jezero_MOLA'},400),
                         ({'a':'Unknown_ASTER','b':'Jezero_MOLA'},404)]:
            resp=self.client.post('/api/analyze',json=req)
            self.assertEqual(resp.status_code,code,resp.text)

    def test_chart_png_and_nodata_numeric(self):
        r=self.client.get('/api/chart',params={'a':'Timanfaya_ASTER','b':'Jezero_MOLA'})
        self.assertEqual(r.status_code,200,r.text[:200])
        self.assertTrue(r.content.startswith(b'\x89PNG\r\n\x1a\n'))
        path=ROOT/'data/regions/Timanfaya_ASTER/DEM.tif'
        d=read_dem(path)
        self.assertAlmostEqual(d['coverage'],1)
        self.assertEqual(len(features(d)),7)

    def test_no_internal_ai_endpoints_exposed(self):
        self.assertEqual(self.client.post('/api/interpret',json={}).status_code,404)
        self.assertEqual(self.client.post('/api/ai-check').status_code,404)

if __name__=='__main__':unittest.main()
