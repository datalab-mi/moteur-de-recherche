import time
from benchmark import ES_HOST, ES_PORT, INDEX_NAME, USER_DATA, ES_DATA, MAPPING_FILE, GLOSSARY_FILE, RAW_EXPRESSION_FILE, DST_DIR, JSON_DIR, META_DIR, sections, test_base_df

import elasticsearch
from elasticsearch import Elasticsearch
from tools.elastic import get_index_name, replace_blue_green, create_index, put_alias, inject_documents, search, index_file, suggest, build_query

print(INDEX_NAME)
es = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT}])

def index(es_host, es_port, index_name, user_data, es_data, mapping_file, glossary_file,
        raw_expression_file, dst_dir, json_dir, meta_dir, sections):
    print("Index")
    es = Elasticsearch([{'host': es_host, 'port': es_port}])

    if es.indices.exists(index=index_name):
        for _ in range(3): # to be sure alias and indexes are removed
            es.indices.delete(index=index_name, ignore=[400, 404])
            es.indices.delete_alias(index='_all',
                name=index_name, ignore=[400, 404])

    # Index creation
    create_index(index_name, user_data, es_data, mapping_file, glossary_file,
            raw_expression_file )

    inject_documents(index_name, user_data, dst_dir, json_dir,
                    meta_path = meta_dir, sections=sections)
    time.sleep(1) # ! important, asynchronous injection


def rank_eval(index_name, rank_body_requests, rank_body_metric):
    return  es.rank_eval(body= {
                              "requests": rank_body_requests,
                              "metric": rank_body_metric
                              },
                         index = INDEX_NAME )
