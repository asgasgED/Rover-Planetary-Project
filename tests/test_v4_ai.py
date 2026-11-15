"""Regression: internal AI debug routes are removed from the public edition."""
import unittest
from fastapi.testclient import TestClient
from backend.api import app

class PublicNoAI(unittest.TestCase):
    def test_no_internal_ai_debug_endpoints(self):
        client=TestClient(app)
        self.assertEqual(client.post('/api/interpret',json={}).status_code,404)
        self.assertEqual(client.post('/api/ai-check').status_code,404)
        self.assertEqual(client.get('/.env').status_code,404)

if __name__=='__main__':unittest.main()
