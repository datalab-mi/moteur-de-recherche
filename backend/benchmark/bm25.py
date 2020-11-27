import argparse
import pytest
import json, os, time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from tools.elastic import get_index_name, replace_blue_green, create_index, put_alias, inject_documents, search, index_file, suggest, build_query
import elasticsearch
from elasticsearch import Elasticsearch
from benchmark.utils import *


'''Getting the arguments
- the path of the Q/A test base
- the path of the environment (ex: .env-bld)
- the list of the metrics
'''

#Parsing argument
parser = argparse.ArgumentParser(description='Evaluation of the metrics')
parser.add_argument('-base-path',dest='base_path', type=str,
    help='Base path ', default = str(Path(__file__).resolve().parent)) # defaut to current path
parser.add_argument('-qr', dest='qr_path', type=str,
    help='the path to Q/A test base file, ex: QR_file.ods', default = 'QR_file.ods')
parser.add_argument('-env', dest='dotenv_path', type=str,
    help='the path to env file, ex: .env-bld', default = '.env-bld')
parser.add_argument('-m', dest='metric', type=str,
    help='metric to evaluate, ex: dcg', default = 'dcg')
parser.add_argument('-index',  action='store_true',
    help='Reindex?')

def main(args):
    args.base_path = Path(args.base_path)
    #Loading the environment
    load_dotenv(dotenv_path=args.base_path / args.dotenv_path, override=True)
    INDEX_NAME = os.getenv('INDEX_NAME')

    USER_DATA = os.getenv('USER_DATA')
    ES_DATA = os.getenv('ES_DATA')

    GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
    RAW_EXPRESSION_FILE = os.getenv('RAW_EXPRESSION_FILE')
    MAPPING_FILE =  os.getenv('MAPPING_FILE')
    THRESHOLD_FILE = os.getenv('THRESHOLD_FILE')

    DST_DIR = os.getenv('DST_DIR')
    JSON_DIR = os.getenv('JSON_DIR')
    META_DIR =  os.getenv('META_DIR')

    ES_PORT=os.getenv('ES_PORT')
    ES_HOST=os.getenv('ES_HOST')

    # Section path
    path_sections = Path(USER_DATA) / 'sections.json'
    if path_sections.exists():
        with open(path_sections, 'r' , encoding = 'utf-8') as json_file:
            sections = json.load(json_file)
    else:
        sections = []

    os.makedirs(ES_DATA, exist_ok=True)

    #Reading files
    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / RAW_EXPRESSION_FILE
    threshold_file = Path(USER_DATA) / THRESHOLD_FILE

    qr_path = args.base_path /args.qr_path
    if qr_path.suffix in ['.ods']:
        test_base_df = pd.read_excel(qr_path, engine="odf") #if odt file
    elif qr_path.suffix == ".csv":
        test_base_df = pd.read_csv(qr_path, encoding= 'utf-8') #if csv file


    es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT}])

    if args.index:
        #Instanciation of elasticsearch

        #Index creation
        for i in range(3): # to be sure alias and indexes are removed
            es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
            es.indices.delete_alias(index='_all',
                name=INDEX_NAME, ignore=[400, 404])


        create_index(INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE, RAW_EXPRESSION_FILE ) #some parameters are stored in the map, that is linked to the index here
        #import pdb; pdb.set_trace()



        inject_documents(INDEX_NAME, USER_DATA, DST_DIR, JSON_DIR,
                        meta_path = META_DIR, sections=sections)
        time.sleep(1) # ! important, asynchronous injection

    #Searching
    rank_body_requests = []
    rank_body_metric = metric_parameters(args.metric) # building the request metric
    query_dict = dict()
    must = {}
    should = {}
    filter = ''
    highlight = []
    #Building the request body
    for id, row in test_base_df.iterrows():

        must = [{"multi_match":{"fields":["question","reponse","titre","mots-cles"],"query":row['Questions']}}]
        body_built, length_of_request = build_query(must, should, filter, INDEX_NAME, highlight, glossary_file=glossary_file, expression_file=expression_file)
        body_query = {"query":body_built["query"]} #removing highlight, to keep?
        request = { "id": str(id), "request": body_query, "ratings": [{ "_index": INDEX_NAME, "_id": "%s"%row['Fiches'], "rating": 1}]}
        rank_body_requests.append(request)
        query_dict[str(id)] = {"query": row['Questions'], "ratings": [{ "_index": INDEX_NAME, "_id": "%s"%row['Fiches'], "rating": 1}]}
    #Metric evaluation
    result = es.rank_eval(body= {
                                  "requests": rank_body_requests,
                                  "metric": rank_body_metric
                                  }, index = INDEX_NAME )

    #print(result)
    for id, req in result["details"].items():
        print("{question} => {answser}".format(question=query_dict[id]["query"],
                        answser=query_dict[id]["ratings"][0]["_id"]))
        print("\n".join([hits['hit']['_id'] for hits  in req['hits']]))
        print("Score : %s"%req["metric_score"])
        print("\n")

    print(20*'-')
    print('Result of %s script'%Path(__file__).resolve().stem)
    print(result["metric_score"])

    print(20*'-')
    return result

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
