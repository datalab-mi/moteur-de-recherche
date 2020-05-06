import os
import pytest

from elasticsearch import Elasticsearch

from application import create_app

NOM_INDEX = 'iga'

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
    return dict(index_name=NOM_INDEX, value='travail illegal')

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
