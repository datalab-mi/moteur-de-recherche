import pytest
import json, os, time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from tools.elastic import get_index_name, replace_blue_green

env_path = '/app/tests/iga/.env-iga'
load_dotenv(dotenv_path=env_path)

INDEX_NAME = os.getenv('INDEX_NAME')

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

def test_reindex(client, app):

    old_index = get_index_name(INDEX_NAME)
    new_index = replace_blue_green(old_index, INDEX_NAME)

    with app.test_client() as c:
        resp = c.get(
            '/admin/%s/reindex'%INDEX_NAME)

    assert resp.status_code == 200, 'Status Code : %s'%resp.status_code
    assert resp.json['color'] == new_index

def test_search(client, app, search_data):
    with app.test_client() as c:
        resp = c.post(
            '/common/search',
            content_type='application/json',
            data = json.dumps(search_data))

    assert resp.status_code == 200, 'Status Code : %s'%resp.status_code

    res= json.loads(
            resp.get_data(as_text=False).decode('utf-8'))

    assert len(res)>0, "No document found"
    #import pdb; pdb.set_trace()
    time.sleep(2)
    assert [hits['_id'] for hits in res['hits']] == ['BF2016-08-16010-dfci.pdf'], 'Find %s'%[hits['_id'] for hits in res['hits']]

def test_upload_file(client, app, form_to_upload):
    # Add document
    with app.test_client() as c:
        resp = c.put(
            '/admin/%s'%form_to_upload['filename'],
            content_type = 'multipart/form-data',
            data = form_to_upload)

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code

    # Delete document
    with app.test_client() as c:
        resp = c.delete(
            '/admin/%s'%form_to_upload['filename'])

    assert resp.status_code == 204, 'Status Code : %s'%resp.status_code

def test_index_file(client, app, index_name, pdf_file):
    # Add document
    with app.test_client() as c:
        resp = c.put(
            '/admin/{index_name}/_doc/{filename}'.format(
            index_name=index_name,
            filename=pdf_file
            ))

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code

    # Delete document
    with app.test_client() as c:
        resp = c.delete(
            '/admin/{index_name}/_doc/{filename}'.format(
            index_name=index_name,
            filename=pdf_file
            ))

    assert resp.status_code == 200, 'Status Code : %s'%resp.status_code

def test_synonym(client, app):
    # Add synonym
    filename = 'glossaire'
    synonym_file = Path(app.config['USER_DATA']) / (filename + '.txt')
    names = ['expressionB','expressionA']
    sep = ' => '
    key = 0
    body = {"expressionA":"dnum","expressionB":"Direction du numérique"}
    res_body = {"expressionA":"_DNUM_","expressionB":"direction numerique"}

    with app.test_client() as c:
        resp = c.put(
            '/admin/synonym/{key}?filename={filename}'.format(
            key=key,
            filename=filename),
            data = json.dumps(body))

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code
    synonym_df = pd.read_csv(synonym_file, sep=sep,header=None, names=names)
    #import  pdb; pdb.set_trace()
    assert synonym_df.iloc[0].to_dict() == res_body

    # Delete synonym
    key = 1
    with app.test_client() as c:
        resp = c.delete(
            '/admin/synonym/{key}?filename={filename}'.format(
            key=key,
            filename=filename))

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code
    synonym_df = pd.read_csv(synonym_file, sep=sep,header=None, names=names)
    #import  pdb; pdb.set_trace()
    assert synonym_df.iloc[0].to_dict() != res_body

def test_expression(client, app):
    # Add synonym
    filename = 'raw_expression'
    synonym_file = Path(app.config['USER_DATA']) / (filename + '.txt')
    names = ['expressionA']
    sep = ';'

    key = 0
    body = {"expressionA":"Direction du numérique"}
    res_body = {"expressionA":"DIRECTION NUMERIQUE"}

    with app.test_client() as c:
        resp = c.put(
            '/admin/synonym/{key}?filename={filename}'.format(
            key=key,
            filename=filename),
            data = json.dumps(body))

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code
    synonym_df = pd.read_csv(synonym_file, sep=sep,header=None, names=names)
    #import  pdb; pdb.set_trace()
    assert synonym_df.iloc[0].to_dict() == res_body

    # Delete synonym
    key = 1
    with app.test_client() as c:
        resp = c.delete(
            '/admin/synonym/{key}?filename={filename}'.format(
            key=key,
            filename=filename))

    assert resp.status_code in [200, 201], 'Status Code : %s'%resp.status_code
    synonym_df = pd.read_csv(synonym_file, sep=sep,header=None, names=names)
    #import  pdb; pdb.set_trace()
    assert synonym_df.iloc[0].to_dict() != res_body
