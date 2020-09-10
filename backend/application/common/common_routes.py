import json, os
from pathlib import Path  # python3 only
import pandas as pd
import glob
import time

from flask import Blueprint, render_template, request, make_response, abort, jsonify, send_from_directory
from flask import current_app as app

from tools.elastic import search as elastic_search
from tools.elastic import build_query as elastic_build_query
from tools.elastic import suggest as elastic_suggest
# Blueprint Configuration
common_bp = Blueprint('common_bp', __name__,url_prefix='/common')
# USER_DATA is known by parent script __init__
if not Path(app.config['USER_DATA']).exists():
    Path(app.config['USER_DATA']).mkdir(parents=True) # recursive

@common_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    return json.dumps({"status": "ok"})

@common_bp.route("/files/<path:path>")
def get_file(path):
    """Download a file."""
    return send_from_directory(app.config['USER_DATA'], path, as_attachment=True)

@common_bp.route("/files")
def list_files():
    """Endpoint to list files on the server."""
    files = []
    for filename in glob.glob(app.config['USER_DATA'] + '/**',recursive=True):
        filename = Path(filename)
        if filename.is_file():
            #filename = Path(filename).relative_to(Path(app.config['USER_DATA']))
            #dict(modified = os.path.getmtime(filename),
            #key=str(filename)

            files.append(dict(key=str(filename.relative_to(Path(app.config['USER_DATA']))),
                              modified=time.ctime(round(filename.stat().st_mtime)),
                              size=filename.stat().st_size * 1024/1000)) # k bytes to kB

    return jsonify(files)

@common_bp.route('/build_query', methods=['POST','OPTIONS'])
def build_query():
    """
    Build only the custom query.
    """

    content = request.get_json(force=True)
    index_name = content.get('index_name', None)
    user_entry = content.get('value', None)
    print(content)
    if not user_entry or not index_name:
        print('Missing keys')
        return json.dumps({})

    GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
    EXPRESSION_FILE = os.getenv('RAW_EXPRESSION_FILE')
    USER_DATA = os.getenv('USER_DATA')

    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / EXPRESSION_FILE

    res = elastic_build_query(user_entry,
                index_name,
                glossary_file,
                expression_file)

    seuil = 4.5
    seuil_affichage = 3.5
    print(10*"*")
    print(res)
    return jsonify(res)

@common_bp.route('/search', methods=['POST'])
def search():
    content = request.get_json(force=True)
    must = content.get('must', None)
    should = content.get('should', None)
    filter = content.get('filter', None)
    highlight = content.get('highlight', None)

    index_name = content.get('index_name', None)
    if  not index_name:
        return

    GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
    EXPRESSION_FILE = os.getenv('RAW_EXPRESSION_FILE')
    USER_DATA = os.getenv('USER_DATA')

    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / EXPRESSION_FILE

    res = elastic_search(must, should, filter, index_name, highlight, 
                glossary_file = glossary_file,
                expression_file = expression_file)

    threshold = 1
    seuil_affichage = 3.5
    res['threshold'] = threshold
    return json.dumps(res)

@common_bp.route('/synonym', methods=['GET'])
def synonym():
    filename = request.args.get('filename', app.config['GLOSSARY_FILE'])
    synonym_file = Path(app.config['USER_DATA']) / (filename + '.txt')

    if "glossaire" in filename:
        names = ['expressionB','expressionA']
        sep = ' => '
    elif "expression" in filename:
        names = ['expressionA']
        sep = ';'
    else:
        return abort(501)

    if synonym_file.exists():
        synonym_df = pd.read_csv(synonym_file, header=None, sep=sep, names=names);
        synonym_df['key'] = synonym_df.index + 1
        return make_response(synonym_df.to_json(orient='records'), 200)

    # In the other cases
    return make_response('', 404)

@common_bp.route('/suggest', methods=['POST'])
def suggest():
    content = request.get_json(force=True)
    user_entry = content.get('content', None)
    index_name = content.get('index_name', None)

    res = elastic_suggest(user_entry,
                index_name)

    return json.dumps(res)#.encode('utf8')
