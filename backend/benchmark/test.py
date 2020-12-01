from benchmark import args, ES_HOST, ES_PORT, INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE, RAW_EXPRESSION_FILE, DST_DIR, JSON_DIR, META_DIR, sections, test_base_df
from benchmark.elasticsearch import index, rank_eval
import json, os, time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from benchmark.utils import *
from sentence_transformers import SentenceTransformer

def main(args):
    #Loading the environment
    print(INDEX_NAME)
    MODEL_NAME = "/app/benchmark/bld/data/sbert.net_models_" + \
        "distilbert-multilingual-nli-stsb-quora-ranking"
    # Embedding with Sentence transformers
    model = SentenceTransformer(MODEL_NAME)

    #Instanciation of elasticsearch
    if args.index:
        index(ES_HOST, ES_PORT, INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE,
                RAW_EXPRESSION_FILE, DST_DIR, JSON_DIR, META_DIR, sections)

        es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT}])
        # Query all documents to retrieve questions
        res = es.search(index=INDEX_NAME, body = {'_source': ['_id', '_type', 'question'],
                'size' : 10000,
                'query': {
                    'match_all' : {}
                }
                })

        all_questions={}
        for r in res['hits']['hits']:
            all_questions[r['_id']]= r['_source']['question'][0]

        qids = list(all_questions.keys())
        questions = [all_questions[qid] for qid in qids]

        embeddings = model.encode(questions, show_progress_bar=False)

        # Update the existing index with embedded vectors
        for qid, embedding in zip(qids, embeddings):
            es.update(index=INDEX_NAME,
                doc_type='_doc',
                id=qid,
                body={
                    "script" : {
                        "source": "ctx._source.question_vector= params.emb",
                        "lang": "painless",
                        "params" : {
                "emb" : embedding
                }
            }
            })
            import pdb; pdb.set_trace()

        time.sleep(1)

    #Searching
    rank_body_requests = []
    rank_body_metric = metric_parameters(args.metric) # building the request metric

    query_dict = dict()

    #Building the request body
    for id, row in test_base_df.iterrows():
        question_embedding = model.encode(row["Questions"])
        #import pdb; pdb.set_trace()
        body_query = {
        "query": {
            "script_score": {
            "query": {
                "match_all": {}
            },
            "script": {
                "source": "cosineSimilarity(params.queryVector, doc['question_vector']) + 1.0",
                "params": {
                "queryVector": question_embedding
                }
            }
            }
        }
        }
        request = { "id": str(id), "request": body_query, "ratings": [{ "_index": INDEX_NAME, "_id": "%s"%row['Fiches'], "rating": 1}]}
        rank_body_requests.append(request)
        query_dict[str(id)] = {"query": row['Questions'], "ratings": [{ "_index": INDEX_NAME, "_id": "%s"%row['Fiches'], "rating": 1}]}

    #import pdb; pdb.set_trace()
    #Metric evaluation
    result = rank_eval(INDEX_NAME, rank_body_requests, rank_body_metric)
    print(20*'-')
    print('Result of %s script'%Path(__file__).resolve().stem)
    print(20*'-')
    #print(json.dumps(result,sort_keys=True, indent=4))
    #import pdb; pdb.set_trace()
    #print(result)
    for id, req in result["details"].items():
        print("{question} => {answser}".format(question=query_dict[id]["query"],
                        answser=query_dict[id]["ratings"][0]["_id"]))
        print("\n".join(["%s (%.02f)"%(hits['hit']['_id'], hits['hit']['_score']) for hits  in req['hits']]))
        print("Score : %s"%req["metric_score"])
        print("\n")

    print(20*'-')
    print('Result of %s script'%Path(__file__).resolve().stem)
    print(result["metric_score"])

    print(20*'-')
    return result

if __name__ == '__main__':
    main(args)
