import json
import os
import tempfile
import unittest
from pathlib import Path

class Tests(unittest.TestCase):
    def test_flujo(self):
        with tempfile.TemporaryDirectory() as d:
            original = json.loads((Path(__file__).resolve().parents[1]/'data'/'conocimiento.json').read_text(encoding='utf-8'))
            db=Path(d)/'conocimiento.json'
            db.write_text(json.dumps(original), encoding='utf-8')
            os.environ['KNOWLEDGE_FILE']=str(db)
            os.environ['MODEL_FILE']=str(Path(d)/'modelo.joblib')
            os.environ['PENDIENTES_FILE']=str(Path(d)/'pendientes.json')
            os.environ['ADMIN_KEY']='clave-test'
            from app import app
            with app.test_client() as client:
                self.assertEqual(client.get('/').status_code, 200)
                self.assertEqual(client.post('/api/chat', json={'pregunta':'hola'}).status_code, 200)
                self.assertEqual(client.post('/api/aprender',json={'pregunta':'nuevo','respuesta':'aprendido'}).status_code,403)
                self.assertEqual(client.post('/api/login',json={'clave':'clave-test'}).status_code,200)
                self.assertTrue(client.post('/api/aprender',json={'pregunta':'cuantos planetas hay','respuesta':'Ocho.'}).json['ok'])
                self.assertEqual(client.post('/api/chat',json={'pregunta':'cuantos planetas hay'}).json['respuesta'],'Ocho.')
                self.assertTrue(client.get('/api/ejemplos').json['ejemplos'])
                rara='qzxjklw vbnteuiorts fhgpqmz'
                self.assertFalse(client.post('/api/chat',json={'pregunta':rara}).json['conocido'])
                pendientes=client.get('/api/pendientes').json['pendientes']
                self.assertTrue(any(p['pregunta']==rara for p in pendientes))
                self.assertTrue(client.post('/api/pendientes/descartar',json={'pregunta':rara}).json['ok'])
                pendientes=client.get('/api/pendientes').json['pendientes']
                self.assertFalse(any(p['pregunta']==rara for p in pendientes))
                self.assertEqual(client.post('/api/logout',json={}).status_code,200)
                self.assertEqual(client.get('/api/ejemplos').status_code,403)
                self.assertEqual(client.get('/api/pendientes').status_code,403)

if __name__=='__main__': unittest.main()
