"""Public release regression tests; use isolated temp folders, never mutate team DEMs."""
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from fastapi.testclient import TestClient

from backend import api, community


def sample_tif(offset=0, scale=1):
    t = from_origin(430000, 9000000, 5000 / 32, 5000 / 32)
    h = np.add.outer(np.arange(32), np.arange(32)).astype('float32') * scale + offset
    with MemoryFile() as mem:
        with mem.open(driver='GTiff', height=32, width=32, count=1, dtype='float32',
                      crs='EPSG:32718', transform=t, nodata=-9999.0) as out:
            out.write(h, 1)
        return mem.read()


class PublicAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        (self.home/'data'/'regions').mkdir(parents=True)
        original = json.loads((api.ROOT/'data'/'catalog.json').read_text('utf8'))
        (self.home/'data'/'catalog.json').write_text(json.dumps(original))
        self.old = (api.CATALOG, api.DATA, community.CATALOG, community.REGIONS,
                    community.IMPORT_SOURCE)
        api.CATALOG = community.CATALOG = self.home/'data'/'catalog.json'
        api.DATA = community.REGIONS = self.home/'data'/'regions'
        community.IMPORT_SOURCE = self.home/'missing'
        community.REQUESTS.clear()
        self.client = TestClient(api.app)

    def tearDown(self):
        (api.CATALOG, api.DATA, community.CATALOG, community.REGIONS,
         community.IMPORT_SOURCE) = self.old
        self.temp.cleanup()

    def upload(self, name='Research sample', body='Tierra', data=None):
        return self.client.post('/api/community-upload',
             data={'title': name, 'body': body, 'public_consent': 'on'},
             files={'file': ('sample.tif', data or sample_tif(), 'image/tiff')})

    def test_public_service_and_no_ai_paths(self):
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ok')
        self.assertEqual(self.client.post('/api/ai-check').status_code, 404)
        self.assertEqual(self.client.post('/api/interpret').status_code, 404)
        self.assertEqual(self.client.get('/.env').status_code, 404)
        self.assertEqual(self.client.get('/backend/api.py').status_code, 404)

    def test_public_dem_published_and_original_catalog_retained(self):
        before=json.loads(api.CATALOG.read_text())
        response=self.upload()
        self.assertEqual(response.status_code, 201, response.text)
        ident=response.json()['id']
        after=json.loads(api.CATALOG.read_text())
        self.assertEqual(len(after['items']), len(before['items'])+1)
        row=next(x for x in after['items'] if x['id']==ident)
        self.assertEqual(row['status'], 'disponible')
        self.assertEqual(row['body'], 'Tierra')
        self.assertTrue(row['user_uploaded'])
        self.assertEqual(len(row['metrics']), 7)
        self.assertEqual(row['area_km2'],25)
        self.assertTrue((api.DATA/ident/'Mapa_2D.png').is_file())
        self.assertEqual(before['items'], after['items'][:-1])

    def test_pairwise_scientific_analysis(self):
        a=self.upload('Terrain A', data=sample_tif()).json()['id']
        b=self.upload('Terrain B', body='Luna', data=sample_tif(11,2)).json()['id']
        result=self.client.post('/api/analyze',json={'a':a,'b':b})
        self.assertEqual(result.status_code,200,result.text)
        self.assertIn('legacy_cosine', result.json())
        self.assertIsNone(result.json()['pixelwise_difference'])
        self.assertEqual(len(result.json()['feature_comparison']),7)

    def test_auto_add_new_team_folder_preserves_existing_entries(self):
        import shutil
        source=self.home/'team_pending'
        source.mkdir()
        community.IMPORT_SOURCE=source
        # Reuse a real, complete six-file deliverable from the team's five examples.
        existing=api.ROOT/'data'/'regions'/'Timanfaya_ASTER'
        if not all((existing/f).is_file() for f in community.SIX):
            self.skipTest('The complete Timanfaya sample is absent')
        clone=source/'Team_Test_ASTER'
        shutil.copytree(existing,clone)
        before=json.loads(api.CATALOG.read_text())
        count=community.import_new_team_deliverables()
        after=json.loads(api.CATALOG.read_text())
        self.assertEqual(count,1)
        self.assertEqual(len(after['items']),len(before['items'])+1)
        self.assertEqual(before['items'], after['items'][:-1])
        self.assertTrue((api.DATA/'Team_Test_ASTER'/'DEM.tif').is_file())
        self.assertEqual(community.import_new_team_deliverables(),0)

    def test_reject_wrong_extent(self):
        with MemoryFile() as mem:
            with mem.open(driver='GTiff',height=8,width=8,count=1,dtype='float32',
                          crs='EPSG:32718',transform=from_origin(1,2,100,100)) as ds:
                ds.write(np.ones((8,8),dtype='float32'),1)
            response=self.upload(data=mem.read())
        self.assertEqual(response.status_code,422)
        self.assertIn('5,000',response.text)

    def test_reject_bad_file(self):
        self.assertEqual(self.upload(data=b'not an image'*50).status_code,422)


if __name__=='__main__':unittest.main()
