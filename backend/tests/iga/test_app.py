import pytest
import json, os

from dotenv import load_dotenv

env_path = '/app/tests/iga/.env-iga'
load_dotenv(dotenv_path=env_path)

NOM_INDEX = os.getenv('NOM_INDEX')

USER_DATA = os.getenv('USER_DATA')
ES_DATA = os.getenv('ES_DATA')

GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
EXPRESSION_FILE = os.getenv('EXPRESSION_FILE')
MAPPING_FILE =  os.getenv('MAPPING_FILE')

PDF_DIR = os.getenv('PDF_DIR')
JSON_DIR = os.getenv('JSON_DIR')


def test_healthcheck(client, app):
    # test that viewing the page renders without template errors
    res = client.get("user/healthcheck")
    print(res)
    assert res.status_code == 200,res

def test_index(client, app):
    with app.test_client() as c:
        resp = c.get(
            '/admin/index',
            content_type='application/json',
            data = json.dumps({'index_name' : NOM_INDEX}))

    assert resp.status_code == 200, 'Status Code : %s'%resp.status_code

def test_search(client, app, search_data):
    with app.test_client() as c:
        resp = c.post(
            '/common/search',
            content_type='application/json',
            data = json.dumps(search_data))

    assert resp.status_code == 200, 'Status Code : %s'%resp.status_code

    resp = json.loads(
            resp.get_data(as_text=False).decode('utf-8'))

    assert len(resp)>0, "No document found"




def test_upload_documents():

    assert True
