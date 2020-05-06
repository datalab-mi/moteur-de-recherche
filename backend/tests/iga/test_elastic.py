import sys, json, os
from pathlib import Path  # python3 only
from dotenv import load_dotenv
from os import environ
import pandas as pd
import elasticsearch
from elasticsearch import Elasticsearch
from shutil import copyfile

from tools.elastic2 import create_index, inject_documents, search
from tools.converter import pdf2json

import pytest
#import pdb; pdb.set_trace()

env_path = '/app/tests/iga2/.env-iga'
load_dotenv(dotenv_path=env_path)

NOM_INDEX = os.getenv('NOM_INDEX')

USER_DATA = os.getenv('USER_DATA')
ES_DATA = os.getenv('ES_DATA')

GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
EXPRESSION_FILE = os.getenv('EXPRESSION_FILE')
MAPPING_FILE =  os.getenv('MAPPING_FILE')

PDF_DIR = os.getenv('PDF_DIR')
JSON_DIR = os.getenv('JSON_DIR')

os.makedirs(ES_DATA, exist_ok=True)

es = Elasticsearch([{'host': 'browser_elasticsearch', 'port': '9200'}])

doc_guyane_eau = "les-bonnes-feuilles-IGA-eau-potable-en-guadeloupe.pdf"

def test_create_index():
    create_index(NOM_INDEX, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE, EXPRESSION_FILE )

@pytest.mark.run(after='test_create_index')
def test_inject_documents():
    metada_file = 'iga.xlsx'
    META_DIR = os.path.join(USER_DATA, PDF_DIR, metada_file)
    inject_documents(NOM_INDEX, USER_DATA, PDF_DIR, JSON_DIR,
                metada_file = META_DIR)

    res = es.get(index=NOM_INDEX, id= doc_guyane_eau)
    assert len(str(res)) > 1000, res

@pytest.mark.run(after='test_inject_documents')
def test_analyse_index():

    # create elasticsearch index

    indices = elasticsearch.client.IndicesClient(es)

    body = {
          "analyzer": "my_analyzer",
          "text": "Sans sa carte national d'identité, il est difficile de rentrer au MI"
        }

    res = indices.analyze(index = NOM_INDEX, body=body)
    print(res)
    print(' '.join([token['token'] for token in res['tokens']]))
    list_synonym = [token['token'] for token in res['tokens'] if token['type'] == 'SYNONYM']
    assert 'cni' in list_synonym, list_synonym

    body = {
          "analyzer": "my_analyzer",
          "text": "Jusqu'ici, les commandes publiques de la DCRFPN me sont inconnus"
        }


    res = indices.analyze(index = NOM_INDEX, body=body)
    print(res)
    print(' '.join([token['token'] for token in res['tokens']]))

    assert 'Jusqu' not in  str(res['tokens'])
    assert 'comandpubliqu' in  str(res['tokens']), 'expresion not taken into account'

    # § sensibilité au accents
@pytest.mark.run(after='test_inject_documents')
def test_search():
    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / EXPRESSION_FILE

    req = 'travail illegal'
    #import pdb; pdb.set_trace()
    hits, length_req, bande = search(req, NOM_INDEX, str(glossary_file), str(expression_file))
    #print(hits, length_req, bande)
    assert  hits[0]['_id'] == 'BF2014-20-14072+Médecine+de+prévention.pdf', 'Found to result %s'%hits[0]['_id']
    assert length_req == 1, length_req
    assert not bande


def test_reindex(client, app, es, dummy_index):
    # test reindex after a change of synonym data
    # First test : change synonym analyser in index

    # test with very basic index
    es.indices.delete(index='dummy_index', ignore=[400, 404])
    # create index
    es.indices.create(index='dummy_index', body=dummy_index)
    # index a document
    name_document = 'babar'
    data = {'content' : 'celeste aime le chat mais pas le chien'}
    es.index(index = 'dummy_index', body=data , id = name_document)

    # change index setting
    settings = dummy_index['settings'].copy()
    settings['analysis']['filter']['my_synonym']['synonyms'] += ["chien => loup"]

    es.indices.close(index='dummy_index')
    es.indices.put_settings(index='dummy_index',body=settings)
    es.indices.open(index='dummy_index')

    es.indices.delete(index='dummy_index', ignore=[400, 404])
    # create index
    es.indices.create(index='dummy_index', body=dummy_index)
    # search
    request = {'query' : {'match_phrase': {'content': 'lion'}}}

    res = es.search(index='dummy_index', body=request)
    assert  res['hits']['hits'][0]['_id'] == 'babar', res
    request = {'query' : {'match_phrase': {'content': 'lion'}}}
    # search
    request = {'query' : {'match_phrase': {'content': 'loup'}}}
    res = es.search(index='dummy_index', body=request)
    assert  res['hits']['hits'][0]['_id'] == 'babar', res


if __name__ == '__main__':
    #test_create_index()
    #test_inject_documents()
    test_analyse_index()
    test_search()
