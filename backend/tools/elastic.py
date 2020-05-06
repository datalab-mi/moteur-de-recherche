# -*- coding: utf-8 -*-
"""Fichier de backend pour gérer les requettes elasticsearch"""

import elasticsearch
from elasticsearch import Elasticsearch
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
from tools.converter import pdf2json, save_json

#%%
#On établit une connection
es = Elasticsearch([{'host': 'elasticsearch', 'port': '9200'}])
indices = elasticsearch.client.IndicesClient(es)

def simple_request(nom_index):
    request = {
        "query": {
            "match_all" : {}
            }
    }

    #D = es.search(index=str(nom_index), size=15, body=request)
    D = es.search(index=str(nom_index_prop), size=15, body=request)
    return D['hits']['hits']

def build_query(req:str, index_name:str,
        glossary_file=None, expression_file=None) -> dict:
    """
    Build the body of the query
    Args:
        index_name : Le nom de l'index où on effectue la recherche
        req : la requête entrèe par l'utilisateur
        expression_file : Le lien pour la liste des expressions clés analysée
        glossary_file : Fichier glossaire
    Returns:
        dict
    """
    from_date, to_date, list_author = None, None, []
    # process gloassary
    #import pdb; pdb.set_trace()
    if glossary_file:
        with open(glossary_file, 'r') as f:
            content = f.read()
        list_glossary = [x.split('=>') for x in str(content).split(
                                '\n') if '=>' in x]

        dic_glossary = {x[0].strip() : x[1].replace(
                        ',', '').strip() for  x  in list_glossary}
        #print(dic_glossary)

        # If user input contains acronym in glossary, add it to req
        for key, val in dic_glossary.items():
            if key in [word.lower() for word in req.split(' ')]:
                req = req + ' ' + val

    if expression_file:
        # process expression
        with open(expression_file, 'r') as f:
            content = f.read()
        list_expression = content.split('\n')[:-1] # last empty line

    # TODO : process all keyword???
    # Liste_acronyme

    print(req)
    #Au début on va analyser la requête

    body = {'analyzer':"french", "text": req}
    analyse = indices.analyze(index= index_name, body = body)

    L = [ananyse_tokens['token'] for ananyse_tokens in analyse["tokens"]]
    print(L)
    analyzed = " ".join(L)
    lenght_of_request = len(L)

    #------------------------Application du filtre 1 -----------------------------
    T = False
    Bande = False
    """ all keyword???
    Bande = False
    for keyword in Liste_acronyme:
        if keyword in analyzed:
            T = True
            break
    """
    # find expression in the request
    req_expression = []
    for expression in list_expression:
        if expression in analyzed :
            for r in ((' ', ''), ('-' ,''), ('_' , '')):
                expression = expression.replace(*r)
            if expression not in req_expression:
                req_expression.append(expression)
                print('req_expression :')
                print(req_expression)

    body = { "query": {
                    "bool": {
                        "must": [],
                        "filter": [],
                        "should": [],
                        "must_not": []
                                }
                        },
                    "highlight" : {
                    "fragment_size" : 300,
                    "number_of_fragments" : 3,
                    "order" : "score",
                    "boundary_scanner" : "sentence",
                    "boundary_scanner_locale" : "fr-FR",
                    "fields":{
                        "content":{}
                        }
                    }
                }


    if len(req.strip()) > 0:
        body["query"]['bool']['must'].append({"simple_query_string": {
                                    "fields" : ["content" , "title"],
                                    "query": req ,
                                    "analyze_wildcard": False
                                                }})

    for key in req_expression:
      body['query']['bool']["should"].append({"match":{
                                      'content' :{
                                          "query" : key,
                                          "boost" : 5
                                                }}})


    if from_date is not None:
        body['query']['bool']["filter"].append({"range" :
                                {"date" : {"gte" : from_date}}
                                             })
    if  to_date is not None:
        body['query']['bool']["filter"].append({"range" :
                                {"date" : {"lte" : to_date}}
                                            })

    for author in list_author:
        author = author.strip()
        if len(author) > 0:
          body['query']['bool']["filter"].append({"match" :
                            {"author" : {"query" : author}}})

    return body, lenght_of_request

def search(req , index_name ,  glossary_file=None, expression_file=None):
    """Fonction qui permet de faire la recherche Elastic dans notre index

    Args:
        index_name : Le nom de l'index où on effectue la recherche
        req : la requête entrèe par l'utilisateur
        expression_file : Le lien pour la liste des expressions clés analysée
        glossary_file : Fichier glossaire
    Output:
        Dictionnaire des résultats de la recherche
    """
    T = False
    Bande = False
    """ all keyword???
    Bande = False
    for keyword in Liste_acronyme:
        if keyword in analyzed:
            T = True
            break
    """
    body, lenght_of_request = build_query(req,
                        index_name,
                        glossary_file,
                        expression_file)

    D = es.search(index = index_name,
                  body = body,
                  size = 10)

    try: #This try is for the case where no match is found
        if not T and D['hits']['hits'][0]["_score"]/lenght_of_request < seuil: #The first filter then the second filter
          Bande = True
    except:
        pass

    return D['hits']['hits'], lenght_of_request , Bande

def corriger(req , nom_index):
  """
    Fonction qui permet de corriger la requête de l'utilisateur
    Arguments:
      nom_index : Le nom de l'index où on effectue la recherche des mots
      req : la requête entrèe par l'utilisateur
    Output:
      Liste des suggestions de correction
"""
  D = es.search(index = nom_index , body = {
  "suggest" : {
   "mytermsuggester" : {
      "text" : req,
      "phrase" : {
         "field" : "Réponse"
       }
    }
  }
  })
  L = []
  for i in range (len(list(D['suggest']['mytermsuggester'][0]['options']))):
    L.append(D['suggest']['mytermsuggester'][0]['options'][i]['text'])
  return L


def create_index(nom_index,
            user_data,
            es_data,
            mapping_file,
            glossary_file=None,
            expression_file=None):

    with open(os.path.join(user_data, mapping_file) , 'r' , encoding = 'utf-8') as json_file:
        map = json.load(json_file)

    if glossary_file:
        print('Use glossary file %s'%glossary_file)
        # Copy glossary and experssion file to elastic search mount volume
        copyfile(os.path.join(user_data, glossary_file),
                os.path.join(es_data, glossary_file))
        map['settings']['index']["analysis"]["filter"]["glossary"].update(
                {"synonyms_path" : os.path.join(es_data, glossary_file)})

    if expression_file:
        print('Use expresion file %s'%expression_file)
        copyfile(os.path.join(user_data, expression_file),
                os.path.join(es_data, expression_file))
        map["settings"]['index']["analysis"]['char_filter']["my_char_filter"].update(
                {'mappings_path' : os.path.join(es_data, expression_file)})

    print(map)
    with open(os.path.join(es_data, mapping_file), 'w') as outfile:
        json.dump(map, outfile)

    es.indices.delete(index=nom_index, ignore=[400, 404])
    # create index
    es.indices.create(index = nom_index, body=map)


def inject_documents(nom_index, user_data, pdf_path=None, json_path=None,
            metada_file=None):

    no_match = 0
    os.makedirs(os.path.join(user_data, json_path), exist_ok=True)

    if metada_file:
        meta_df = pd.read_excel(metada_file)
        #meta_df.set_index('Unnamed: 0' , inplace = True)

    for name_document in os.listdir(os.path.join(user_data, pdf_path)):
        if name_document.endswith(".pdf"):
            try:
                path_document = os.path.join(user_data, pdf_path, name_document)
                print('Read %s'%path_document)
                data = pdf2json(path_document)

                if metada_file:
                    meta = meta_df.loc[meta_df['file'] == name_document, :]

                    if not meta.empty:

                        #data['titre'] = str(meta['titre'].values[0])
                        #data['Date'] = "%d-01-01"%meta['annee2'].values[0].astype(int)
                        #data['Auteurs'] = str(meta['nomaut1'].values[0])
                        meta = meta.iloc[0]
                        meta['date'] = meta['date'].strftime('%Y-%m-%d')
                        data.update(meta)
                    else:
                        no_match += 1
                        continue

                #with open(os.path.join(user_data, json_path, name_document.replace('.pdf','.json')) , 'w', encoding='utf-8') as f:
                #    json.dump(data, f, ensure_ascii=False)
                save_json(data, os.path.join(user_data, json_path, name_document.replace('.pdf','.json')))
                es.index(index = nom_index, body=data , id = name_document)
                print('Document %s just uploaded'% name_document)

            except Exception as e:
                print(e)
                #break
                print(20*'*')
                print('Error, cannot upload %s'%name_document)
                print(20*'*')

    print("There is %s documents without metadata match"%no_match)

def refresh(nom_index):
    es.indices.refresh(index = nom_index)
    return


if __name__ == '__main__':

    NOM_INDEX = 'prod'
    USER_DATA = '/data/user'
    ES_DATA = '/usr/share/elasticsearch/data/extra'

    GLOSSARY_FILE = 'glossaire.txt'
    EXPRESSION_FILE = 'syn_expressions_metier.txt'
    MAPPING_FILE = 'map.json'
    METADATA_FILE = 'METADATA.xlsx'

    PDF_DIR = 'Data_Pdf'
    JSON_DIR = 'Data_Json'

    create_index(NOM_INDEX, USER_DATA, ES_DATA, MAPPING_FILE,
                GLOSSARY_FILE,
                EXPRESSION_FILE)

    inject_documents(NOM_INDEX, USER_DATA, PDF_DIR, JSON_DIR,
            metada_file = METADATA_FILE)
