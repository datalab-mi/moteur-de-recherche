import json
from pathlib import Path  # python3 only
from os import environ

from flask import current_app as app
from flask import Blueprint, render_template, request, make_response, abort, jsonify, send_from_directory

from tools.elastic import create_index, inject_documents

# Blueprint Configuration
admin_bp = Blueprint('admin_bp', __name__,url_prefix='/admin')

print(app.config)

@admin_bp.route('/cluster', methods=['GET'])
def cluster():
    elastic_info = Elasticsearch.info(client)
    return json.dumps(elastic_info, indent=4 )


@admin_bp.route('/index', methods=['GET'])
def index():
    """(Re)index after a mapping change
    """
    content = request.get_json(force=True)
    index_name = content.get('index_name', app.config['NOM_INDEX'])

    create_index(app.config['NOM_INDEX'],
                 app.config['USER_DATA'],
                 app.config['ES_DATA'],
                 app.config['MAPPING_FILE'],
                 app.config['GLOSSARY_FILE'],
                 app.config['EXPRESSION_FILE'])

    # inject only json
    metada_file = 'iga.xlsx'
    META_DIR = Path(app.config['USER_DATA']) / app.config['PDF_DIR'] / metada_file

    inject_documents(index_name,
                    app.config['USER_DATA'],
                    pdf_path = app.config['PDF_DIR'],
                    json_path = app.config['JSON_DIR'],
                    metada_file = META_DIR)

    return jsonify(success=True)
