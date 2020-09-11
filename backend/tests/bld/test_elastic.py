import sys, json, os, time
from pathlib import Path  # python3 only
from dotenv import load_dotenv
from os import environ
import pandas as pd
import elasticsearch
from elasticsearch import Elasticsearch
from shutil import copyfile

from tools.elastic import create_index, get_alias, put_alias, delete_alias, get_index_name, replace_blue_green, inject_documents, search, index_file, suggest
from tools.converter import pdf2json

import pytest
#import pdb; pdb.set_trace()

env_path = '/app/tests/bld/.env-bld'
load_dotenv(dotenv_path=env_path)

INDEX_NAME = os.getenv('INDEX_NAME')

USER_DATA = os.getenv('USER_DATA')
ES_DATA = os.getenv('ES_DATA')

GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
EXPRESSION_FILE = os.getenv('EXPRESSION_FILE')
RAW_EXPRESSION_FILE = os.getenv('RAW_EXPRESSION_FILE')

MAPPING_FILE =  os.getenv('MAPPING_FILE')

PDF_DIR = os.getenv('PDF_DIR')
ODT_DIR = os.getenv('ODT_DIR')
JSON_DIR = os.getenv('JSON_DIR')
META_DIR =  os.getenv('META_DIR')

os.makedirs(ES_DATA, exist_ok=True)

es = Elasticsearch([{'host': 'elasticsearch', 'port': '9200'}])

def test_create_index():
    # Clear
    for i in range(3): # to be sure alias and indexes are removed
        es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
        es.indices.delete_alias(index=[INDEX_NAME + '_blue', INDEX_NAME + '_green'],
            name=INDEX_NAME, ignore=[400, 404])


    create_index(INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE, RAW_EXPRESSION_FILE )

@pytest.mark.run(after='test_create_index')
def test_inject_documents(sections):

    doc = 'moteur de recherche.odt'
    
    inject_documents(INDEX_NAME, USER_DATA, ODT_DIR, JSON_DIR,
                meta_path = META_DIR, doc_type='odt', sections=sections)

    res = es.get(index=INDEX_NAME, id=doc)
    assert len(str(res)) > 100, res

@pytest.mark.run(after='test_inject_documents')
def test_analyse_index():

    # create elasticsearch index

    indices = elasticsearch.client.IndicesClient(es)

    body = {
          "analyzer": "my_analyzer",
          "text": "La dnum du Ministère de l'interieur"
        }

    # Test synonym
    res = indices.analyze(index = INDEX_NAME, body=body)
    print(res)
    print(' '.join([token['token'] for token in res['tokens']]))
    list_synonym = [token['token'] for token in res['tokens'] if token['type'] == 'SYNONYM']
    assert 'mi' in list_synonym, list_synonym

    # test expression
    body = {
          "analyzer": "my_analyzer",
          "text": "transformation numérique"
        }
    res = indices.analyze(index = INDEX_NAME, body=body)
    print(' '.join([token['token'] for token in res['tokens']]))
    #import pdb; pdb.set_trace()

@pytest.mark.run(after='test_inject_documents')
def test_search():
    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / RAW_EXPRESSION_FILE

    doc = 'création+de+la+DNUM.odt'
    req = 'Depuis quand date la direction du Numérique?'
    time.sleep(2)
    res = search(req, INDEX_NAME, str(glossary_file), str(expression_file))
    #import pdb; pdb.set_trace()

    #print(hits, length_req, bande)
    assert  res['hits'][0]['_id'] == doc, 'Found to result %s'%res['hits'][0]['_id']
    assert res['length'] == 4, res['length']
    assert not res['band']

    # test expression
    req = "transformation numérique"
    res= search(req, INDEX_NAME, str(glossary_file), str(expression_file))
    #import pdb; pdb.set_trace()
    assert res['hits'][0]['_score']  > 6, 'boosting no taken into account'

# Test test_reindex and suggest already in iga test folder


if __name__ == '__main__':
    test_create_index()
    test_inject_documents()
    test_analyse_index()
    test_search()
