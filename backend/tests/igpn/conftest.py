import os
import pytest
from pathlib import Path

from elasticsearch import Elasticsearch

from application import create_app

INDEX_NAME = 'iga'

USER_DATA = 'tests/iga/data'
filename = 'ignit_pnigitis'

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    app = create_app()
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def search_data():
    return dict(index_name=INDEX_NAME,
                content='foret',
                author='GRANJEANT',
                to_date='2017-06-06',
                from_date='2015-06-06')

@pytest.fixture
def es():
    return Elasticsearch([{'host': 'elasticsearch', 'port': '9200'}])

@pytest.fixture
def dummy_index():
    return {
          "settings": {
            "analysis": {
              "filter" : {
                "my_synonym": {
                  "type": "synonym",
                  "synonyms": [
                    "chat => lion"
                      ]
                  }
            },
              "analyzer": {
                "my_analyzer": {
                  "tokenizer": "standard",
                  "filter": [
                    "my_synonym"
                    ]
                  }
                }
            }
          },
          "mappings":{
              "properties": {
                 "content": {
                    "type": "text",
                    "analyzer" : "my_analyzer",
                    "search_analyzer" : "my_analyzer"
                }
              }
            }
        }

@pytest.fixture
def form_to_upload():
    yield dict(author= 'babar',
                date= '2020-05-04',
                filename=filename + '.pdf',
                file=(open(USER_DATA + '/' + filename + '.pdf', "rb"), filename) )

@pytest.fixture
def file_name():
    return filename

@pytest.fixture
def index_name():
    yield INDEX_NAME

@pytest.fixture
def pdf_file():
    yield filename
