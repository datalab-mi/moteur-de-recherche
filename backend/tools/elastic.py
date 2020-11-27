# -*- coding: utf-8 -*-
"""Backend scrpits to handle Elastic Search (ES) queries"""

import elasticsearch
from elasticsearch import Elasticsearch, NotFoundError
import os
import base64
import json
import logging
import datetime
from os.path import expanduser
from os import environ
import unicodedata
from datetime import date
from copy import deepcopy
from pathlib import Path
from shutil import copyfile
import pandas as pd
from tools.converter import pdf2json, odt2json, save_json
from tools.utils import empty_tree, _finditem
import json
import time
import re


#On établit une connection
es = Elasticsearch([{'host': 'elasticsearch', 'port': '9200'}])
indices = elasticsearch.client.IndicesClient(es)

def simple_request(index_name, size):
    """Perform ES search on all documents of an index. Equivalent to index/_search
    Args:
        index_name (str): The index on the search is done
        size (int): Number of maximum results to return
    Returns:
        list: the hits return by ES
    """
    request = {
        "query": {
            "match_all" : {}
            }
    }

    D = es.search(index=str(INDEX_NAME_prop), size=size, body=request)
    return D['hits']['hits']

def clean(expression:str, index_name:str, analyzer="clean_analyser"):
    """
    Apply lowercase, filter and stop word
    Args:
        Expression (str): The string to clean
        index_name (str): The index where analysers lie on
        analyzer (str): The ES analyser to use
    Returns:
        list: ES tokens
    """
    body = {'analyzer': analyzer, "text": expression}
    analyse = indices.analyze(index= index_name, body = body)
    list_token = [x['token'] for x  in analyse['tokens'] if 'token' in x]
    return list_token


def build_query(must: dict, should: dict, filter: dict, index_name: str,
            highlight: list,
            glossary_file=None, expression_file=None) -> dict:
    """
    Build the body of the ES query
    Args:
        must (dict): the must request
        should (dict): the should request
        filter (str): the filter request
        index_name (str): The index name
        highlight (list): List of keys to highlight
        expression_file (str): Expression file path
        glossary_file (str): Acronym file path
    Returns:
        dict: The ES query to pass
    """

    length_of_request = 0
    list_expression = []
    # TODO : process all keyword???
    # Liste_acronyme
    if must:
        if expression_file:
            # process expression
            with open(expression_file, 'r') as f:
                content = f.read()
            list_expression = [x.lower().split(' ') for x in str(content).split('\n')]
            list_expression = [''.join(x) for x in list_expression]
        else:
            list_expression = []

        req = " ".join([_finditem(x, "query") for x in must])
        #Au début on va analyser la requête
        body = {'analyzer':"my_analyzer", "text": req}
        analyse = indices.analyze(index= index_name, body = body)

        analyzed = [ananyse_tokens['token'] for ananyse_tokens in analyse["tokens"]]
        print(analyzed)

        length_of_request = len(analyzed)


    #------------------------Application du filtre 1 -----------------------------
    T = False
    Bande = False
    """ all keyword???
    Bande = FalseTHRESHOLD_FILE_file
    for keyword in Liste_acronyme:
        if keyword in analyzed:
            T = True
            break
    """
    # find expression in the request
    req_expression = []

    for expression in list_expression:
        if expression in analyzed :
            req_expression.append(expression)
            print('req_expression :')
            print(req_expression)

    #import pdb; pdb.set_trace()
    body = { "query": {
                    "bool": {
                        "must": [],
                        "filter": [],
                        "should": [],
                        "must_not": []
                                }
                        },
            "highlight" : {
                "pre_tags" : ["<mark>"],
                "post_tags" : ["</mark>"],
                "fragment_size" : 300,
                "number_of_fragments" : 3,
                "order" : "score",
                "boundary_scanner" : "sentence",
                "boundary_scanner_locale" : "fr-FR",
                "fields":{}
                    }
                }


    if must:
        body["query"]['bool']['must'] += must

    if filter:
        body['query']['bool']["filter"] += filter

    if should:
        body["query"]['bool']['should'] += should

    # add boosting in should for expressions
    #import pdb; pdb.set_trace()
    for key in req_expression:
      body['query']['bool']["should"].append({"multi_match":{
                                        'fields': [_finditem(x, "fields") for x in must][0],
                                        'boost': 5, # can be boosted per fields with ^
                                         "query" : '_' + key + '_',
                                                }})

    if highlight:
        for field in highlight:
            body['highlight']['fields'].update({field: {}})
    #import pdb; pdb.set_trace()

    print(body)

    return body, length_of_request

def search(must: dict, should: dict, filter: dict, index_name: str,
            highlight: list,
            glossary_file=None, expression_file=None, threshold_file=None):

    """Perform the ES search
    Args:
        must (dict): the must request
        should (dict): the should request
        filter (str): the filter request
        index_name (str): The index name
        highlight (list): List of keys to highlight
        expression_file (str): Expression file path
        glossary_file (str): Acronym file path
        threshold_file (str): threshold file path
        size: number of documents to display (display threshold)
    Returns:
        dict:
    """
    T = False
    Bande = False


    if threshold_file and threshold_file.exists():
        with open(threshold_file) as json_file:
            thresholds = json.load(json_file)
    else:
        thresholds = {}

    #import pdb; pdb.set_trace()
    #req = [_finditem(x, "query") for x in must]
    #print(req)

    if (must or should or filter):
        body, length_of_request = build_query(must, should, filter, index_name,
                    highlight,
                    glossary_file=glossary_file, expression_file=expression_file)
        time.sleep(0.5)
        D = es.search(index = index_name, body = body,size = thresholds.get('d_threshold', int(1000)),request_cache=False)
    else:
        length_of_request = None
        D = es.search(index = index_name,
                      body = {
                            "query": {
                                "match_all": {}
                            }
                        },
                    size = thresholds.get('d_threshold', int(1000))
                    )
        thresholds['r_threshold'] = 0

    try: #This try is for the case where no match is found
        if not T and D['hits']['hits'][0]["_score"]/length_of_request < seuil: #The first filter then the second filter
          Bande = True
    except:
        pass

    return {'hits': D['hits']['hits'],
            'length': length_of_request , 'band': Bande,
            'r_threshold': thresholds.get('r_threshold', 1)}


def suggest(req: str , index_name: str):
    """Perform a ES search in  suggest mode
    Args:
        index_name (str): The index name
        req: The user entry
    Returns:
        list: List of suggestions

    """
    D = es.search(index = index_name , body = {
      "suggest": {
        "text" : req,
        "simple_phrase" : {
          "phrase" : {
            "field" : "content.trigram",
            "highlight": {
                "pre_tag": "<b>",
                "post_tag": "</b>"
              },
            "size" : 3,
            "direct_generator" : [ {
              "field" : "content.trigram",
              "suggest_mode" : "always"
            }, {
              "field" : "content.reverse",
              "suggest_mode" : "always",
              "pre_filter" : "reverse",
              "post_filter" : "reverse"
            } ]
          }
        }
      }
    })

    res = []
    for suggestion in D['suggest']['simple_phrase'][0]['options']:
        res.append(suggestion)
    return res


def get_index_name(alias_name: str):
    """Get index name of alias
        Args:
            alias_name (str): The alias name
        Returns:
            str: The index name
    """
    try:
        res = es.indices.get_alias(name=alias_name)
        if len(res.keys()) == 1 and list(res.keys())[0] != "":
            index_name = list(res.keys())[0]
        else:
            raise Exception
    except NotFoundError:
        # create alias pointing to the blue index.
        index_name = alias_name + '_blue'
        es.indices.put_alias(index=alias_name, name=index_name)
    except Exception as err:
        print('Catch unexpected error: ', err)
    return index_name

def replace_blue_green(index_name: str, alias_name: str):
    """Change the index color
    Args:
        alias_name (str): The alias name
        index_name (str): The old index name

    Returns:
        str: The new index name
    """
    if 'blue' in index_name:
        index_name = index_name.replace('blue', 'green')
    elif 'green' in index_name:
        index_name = index_name.replace('green', 'blue')
    else:
        raise Exception

    return index_name

def put_alias(index_name: str, alias_name: str):
    es.indices.put_alias(index=index_name, name=alias_name)

def delete_alias(index_name: str, alias_name: str):
    es.indices.delete_alias(index=index_name, name=alias_name, ignore=[400, 404])

def get_alias(alias_name: str):
    return es.indices.get_alias(name=alias_name)

def exists(index_name: str):
    return es.indices.exists(index_name)


def create_index(index_name: str,
            user_data: str,
            es_data: str,
            mapping_file: str,
            glossary_file=None,
            expression_file=None):
    """Create in ES the index.
    Populate the mapping file with synonym paths, then dumps in es data directory
    and finally create the index in ES.
    Args:
        index_name (str): The old index name
        user_data (str): Path of data in backend docker
        es_data (str): Path of data in ES docker, to store mapping and synonyms files
        mapping_file (str): mapping file name
        expression_file (str): Expression file name
        glossary_file (str): Acronym file name
    """
    os.makedirs(es_data, exist_ok=True)
    synonym_file = os.path.join(es_data, 'synonym.txt')
    synonym_search_file = os.path.join(es_data, 'search_synonym.txt')

    with open(os.path.join(user_data, mapping_file) , 'r' , encoding = 'utf-8') as json_file:
        map = json.load(json_file)
    # Copy glossary and experssion file to elastic search mount volume

    # for index analyser
    with open(synonym_file, 'w') as outfile:
        if glossary_file:
            print('Use glossary file %s'%glossary_file)
            with open(os.path.join(user_data, glossary_file), 'r') as f1:
                outfile.write(f1.read())
        outfile.write('\n')
        if expression_file:
            print('Use expresion file %s'%expression_file)
            with open(os.path.join(user_data, expression_file), 'r') as f2:
                # Create expression file from raw_expression
                list_expression = [x.lower().split(' ') for x in str(f2.read()).split('\n') if x != '']
                list_expression = [' '.join(x) + ' => ' + '_' + ''.join(x) + '_, ' + ', '.join(x) for x in list_expression]
                str_expression = '\n'.join(list_expression)
                outfile.write(str_expression)
        else:
            outfile.write('')

    map['settings']["analysis"]["filter"]["synonym"].update(
            {"synonyms_path" : os.path.join(es_data, synonym_file)})

    # for search analyser
    with open(synonym_search_file, 'w') as outfile:
        if glossary_file:
            print('Use glossary file %s'%glossary_file)
            with open(os.path.join(user_data, glossary_file), 'r') as f1:
                list_glossary = [x.split(' => ') for x in str(f1.read()).split(
                                        '\n') if '=>' in x]
                list_glossary = [x[0].replace(' ', ', ') + ' => ' + x[1] for x in list_glossary]
                str_glossary = '\n'.join(list_glossary)
                outfile.write(str_glossary)
        outfile.write('\n')
        if expression_file:
            print('Use expresion file %s'%expression_file)
            with open(os.path.join(user_data, expression_file), 'r') as f2:
                # Create expression file from raw_expression
                list_expression = [x.lower().split(' ') for x in str(f2.read()).split('\n') if x != '']
                list_expression = [' '.join(x) + ' => ' + '_' + ''.join(x) + '_, ' + ', '.join(x) for x in list_expression]
                str_expression = '\n'.join(list_expression)
                outfile.write(str_expression)
        else:
            outfile.write('')

    map['settings']["analysis"]["filter"]["search_synonym"].update(
            {"synonyms_path" : os.path.join(es_data, synonym_search_file)})

    # print(map)
    with open(os.path.join(es_data, mapping_file), 'w') as outfile:
        json.dump(map, outfile)

    # Drop index
    es.indices.delete(index=index_name, ignore=[400, 404])
    # create index
    es.indices.create(index=index_name, body=map)


def inject_documents(index_name: str, user_data: str, dst_path: str, json_path: str,
            meta_path=None, sections=[]):

    """Inject in ES all documents present in dst_path.
    Args:
        index_name (str): The index name
        user_data (str): Path of data in backend docker
        dst_path (str): relative path of the folder which contains
            the documents to index
        json_path (str): relative path of the folder which contains
            the content of the documents
        meta_path (str): relative path of the folder which contains
            the meta data of the documents
        sections (list): In case of odt document, contains the sections to read
    """
    no_match = 0

    (Path(user_data) / json_path).mkdir(parents=True, exist_ok=True)
    # empty it in case
    empty_tree(Path(user_data) / json_path)

    for path_document in (Path(user_data) / dst_path).iterdir():
        try:
            #path_document = pdf_path / filename
            print('Read %s'%str(path_document))

            filename = path_document.name
            index_file(filename, index_name, user_data,
                        dst_path, json_path, meta_path, sections=sections)
            print('Document %s just uploaded'% path_document)

        except Exception as e:
            no_match += 1
            print(e)
            #break
            print(20*'*')
            print('Error, cannot upload %s'%path_document)
            print(20*'*')

    print("There is %s documents without metadata match"%no_match)

def index_file(filename: str, index_name: str, user_data: str, dst_path: str,
            json_path: str, meta_path,  sections=[]):
    """Inject in ES the document <filename>
    Args:
        filename (str): The document to index
        index_name (str): The index name
        user_data (str): Path of data in backend docker
        dst_path (str): relative path of the folder which contains
            the documents to index
        json_path (str): relative path of the folder which contains
            the content of the documents
        meta_path (str): relative path of the folder which contains
            the meta data of the documents
        sections (list): In case of odt document, contains the sections to read
    """
    filename = Path(filename)
    path_document = Path(user_data) / dst_path / filename
    #import pdb; pdb.set_trace()
    if  filename.suffix == '.pdf':
        data = pdf2json(str(path_document))
    elif  filename.suffix == '.odt':
        data = odt2json(str(path_document), sections)
    else:
        raise Exception("Format not supported")

    # Clean fields specified in sections.json
    for entry in sections:
        if entry.get('clean',False):
            for key in data :
                if key == entry.get("field",None) :
                    if type(data[key]) == list:
                        y = []
                        for x in data[key]:
                            y += [" ".join(clean(x, index_name))]
                        data[key] = y
                    else:
                        data[key] = clean(data[key], index_name)


    #import pdb; pdb.set_trace()
    path_meta =  Path(user_data) / meta_path / (path_document.stem + '.json')
    path_json =  Path(user_data) / json_path / (path_document.stem + '.json')

    if path_meta.exists():
        with open(path_meta, 'r' , encoding = 'utf-8') as json_file:
            meta = json.load(json_file)
            data.update(meta)
    # clean date field
    if "date" in data:
        data["date"] = re.sub(r'[^\d\/]','',data["date"]) # remove all caractere ! / or digit
        data["date"] = data["date"].replace("//",'/')
    save_json(data, path_json)

    res = es.index(index = index_name, body=data , id = path_document.name)
    return res

def delete_file(filename, index_name):
    """Inject in ES the document <filename>
    Args:
        filename (str): The document to index
        index_name (str): The index name
    Returns:
        HTTP error code
    """
    try:
        res = es.delete(index = index_name, id = filename)
        return 200, res
    except elasticsearch.exceptions.NotFoundError as e:
        return e.status_code, e.info
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

def get_unique_keywords(index_name: str, field: str) -> list:
    """Get unique keywords list from an filed of type keyword
    Args:
        field (str): field name
        index_name (str): The index name
    Returns:
        List: The list of unique keywords
    """
    body = {
          "size": 0,
          "aggs": {
            field: {
              "terms": { "field": field,
                        "size": int(1e4) }
            }
          }
        }
    res = es.search(index=index_name, body=body)
    return [x['key'] for x in res['aggregations'][field].get('buckets', [{}])]

if __name__ == '__main__':

    INDEX_NAME = 'prod'
    USER_DATA = '/data/user'
    ES_DATA = '/usr/share/elasticsearch/data/extra'

    GLOSSARY_FILE = 'glossaire.txt'
    EXPRESSION_FILE = 'syn_expressions_metier.txt'
    MAPPING_FILE = 'map.json'
    METADATA_FILE = 'METADATA.xlsx'

    PDF_DIR = 'Data_Pdf'
    JSON_DIR = 'Data_Json'

    create_index(INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE,
                GLOSSARY_FILE,
                EXPRESSION_FILE)

    inject_documents(INDEX_NAME, USER_DATA, PDF_DIR, JSON_DIR,
            metada_file = METADATA_FILE)
