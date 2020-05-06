import json, os
from pathlib import Path  # python3 only
import glob
import time

from flask import Blueprint, render_template, request, make_response, abort, jsonify, send_from_directory
from flask import current_app as app

from tools.elastic import search as elastic_search
from tools.elastic import build_query as elastic_build_query

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','md'}

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@common_bp.route("/upload", methods=["POST"])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        print(request.files)
        if 'file' not in request.files:
            print('no file')
            return abort(500)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            print('no filename')
            abort(500)
        if file and allowed_file(file.filename):
            filename = file.filename
            path = Path(app.config['USER_DATA']) / filename
            print(path)
            file.save(path)
            return jsonify(success=True)

        else:
            abort(500)




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
    EXPRESSION_FILE = os.getenv('EXPRESSION_FILE')
    USER_DATA = os.getenv('USER_DATA')

    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / 'analysed_expression.txt'

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
    content = request.json
    user_entry = content.get('value', None)
    index_name = content.get('index_name', None)
    if not user_entry or not index_name:
        return

    GLOSSARY_FILE = os.getenv('GLOSSARY_FILE')
    EXPRESSION_FILE = os.getenv('EXPRESSION_FILE')
    USER_DATA = os.getenv('USER_DATA')

    glossary_file = Path(USER_DATA) / GLOSSARY_FILE
    expression_file = Path(USER_DATA) / 'analysed_expression.txt'

    res = elastic_search(user_entry,
                index_name,
                glossary_file,
                expression_file)

    seuil = 4.5
    seuil_affichage = 3.5
    return json.dumps(res)
