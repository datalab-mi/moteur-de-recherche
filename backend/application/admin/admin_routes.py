import json
from json.decoder import JSONDecodeError
from pathlib import Path  # python3 only
import pandas as pd
from os import environ

from flask import current_app as app
from flask import Blueprint, render_template, request, make_response, abort, jsonify, send_from_directory

from tools.elastic import index_file as elastic_index_file
from tools.elastic import delete_file as elastic_delete_file
from tools.elastic import create_index, get_alias, put_alias, delete_alias, exists, get_index_name, replace_blue_green, inject_documents, clean

from tools.utils import empty_tree

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','md','odt'}

# Blueprint Configuration
admin_bp = Blueprint('admin_bp', __name__,url_prefix='/admin')

print(app.config)

@admin_bp.route('/cluster', methods=['GET'])
def cluster():
    elastic_info = Elasticsearch.info(client)
    return json.dumps(elastic_info, indent=4 )


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Section path
path_sections = Path(app.config['USER_DATA']) / 'sections.json'
if path_sections.exists():
    with open(path_sections, 'r' , encoding = 'utf-8') as json_file:
        sections = json.load(json_file)
else:
    sections = []

@admin_bp.route("/files")
@admin_bp.route("/files/<path:path>", methods=["PUT","DELETE"])
def get_file(path=''):
    """Add, replace or delete a file or folder name in the file system USER_DATA
    Args:
        path (str): The relative path of the document or folder
    Returns: Usual HTTP status code
        204: Delete successful
        404: Delete unsuccessful
        200: Create
        201: Update
        TODO : Creatagte/update for folder
    """
    dir = Path(app.config['USER_DATA']) / path
    if request.method == 'DELETE':
        if dir.is_file():
            dir.unlink()
            return make_response(jsonify(sucess=True), 204)

        elif dir.is_dir():
            empty_tree(dir)
            return make_response(jsonify(sucess=True), 204)

        else:
            return make_response(jsonify(sucess=False), 404)
    elif request.method == 'PUT':
        if dir.is_file():
            status = 200
        else:
            status = 201
        file = request.files.get('file', False)
        if file and allowed_file(str(dir)):
            # save file
            file.save(dir)
            print("save %s"%dir)
        else:
            status = 404
        return  make_response(jsonify(sucess=True), status)

@admin_bp.route("/<filename>", methods=["PUT","DELETE"])
def upload_file(filename: str):
    """Add, replace or delete a document in order to index it in ES
     in the file system USER_DATA,
    Args:
        filename (str): The relative path of the document
        file (binary): Inside the HTTP POST request
        meta (form): HTTP form data
    Returns: Usual HTTP status code
        204: Delete successful
        404: Delete unsuccessful
        200: Create
        201: Update
        500: Server abort
    """
    path_file = Path(app.config['USER_DATA']) / app.config['DST_DIR'] / filename
    path_meta = Path(app.config['USER_DATA']) / app.config['META_DIR'] / filename
    path_json = Path(app.config['USER_DATA']) / app.config['JSON_DIR'] / filename

    path_meta = path_meta.with_suffix('').with_suffix('.json') # replace extension
    path_json = path_json.with_suffix('').with_suffix('.json') # replace extension

    if request.method == 'DELETE':
        if path_file.exists():
            path_file.unlink()
            path_meta.unlink(missing_ok=True)
            path_json.unlink(missing_ok=True)
            return make_response(jsonify(sucess=True), 204)

        else:
            return make_response(jsonify(sucess=False), 404)

    elif request.method == 'PUT':
        if path_file.exists():
            status = 200
        else:
            status = 201

        # ? check if the post request has the file part ?
        file = request.files.get('file', False)
        # if user does not select file, browser also
        # submit an empty part without filename

        if file and allowed_file(filename):
            # save file
            file.save(path_file)
            print("save %s"%path_file)
        else:
            status = 202
        # save meta
        if path_meta.parent.exists():
            with open(path_meta , 'w', encoding='utf-8') as f:
                form_to_save = {}
                # Need to format array in request.form ...
                for k, v in request.form.items():
                    try :
                        form_to_save[k] = json.loads(v)
                    except JSONDecodeError as e:
                        form_to_save[k] = v
                json.dump(form_to_save, f, ensure_ascii=False)
                print("save %s"%path_file)
        else:
            print("%s doesn't exist"%path_meta.parent)

        return  make_response(jsonify(sucess=True), status)

    else:
        abort(500)


@admin_bp.route("/<index_name>/_doc/<filename>", methods=["DELETE", "PUT"])
def index_file(index_name: str, filename: str):
    """Add, replace or delete a document in Elastic Search (ES)
    Args:
        index_name (str): ES index
        filename (str): The file name
    Returns: Usual HTTP status codes
        204: Delete
        200: Create
        201: Update
        500: Server abort
    """

    if not index_name or not filename:
        print('Missing keys')
        return abort(500)
    if request.method == 'PUT':
        res = elastic_index_file(filename, index_name,
                    app.config['USER_DATA'],
                    app.config['DST_DIR'],
                    app.config['JSON_DIR'],
                    app.config['META_DIR'], sections=sections)
        status = 201 if res['result'] == 'created' else 200 if res['result'] == 'updated' else 500
        return make_response(res, status)

    elif request.method == 'DELETE':
        status, res = elastic_delete_file(filename, index_name)
        return make_response(res, status)


@admin_bp.route('/<index_name>/reindex', methods=['GET'])
def index(index_name: str):
    """(Re)index after a mapping change
    Args:
        index_name (str): ES index
    """
    #content = request.get_json(force=True)
    #index_name = content.get('index_name', app.config['INDEX_NAME'])
    #index_name  = index_name if index_name else app.config['INDEX_NAME']

    if not exists(index_name): # init if no index in ES
        old_index = index_name + '_green'
        new_index = index_name + '_blue'
    else:
        old_index = get_index_name(index_name)
        new_index = replace_blue_green(old_index, index_name)

    create_index(new_index,
                 app.config['USER_DATA'],
                 app.config['ES_DATA'],
                 app.config['MAPPING_FILE'],
                 app.config['GLOSSARY_FILE'],
                 app.config['RAW_EXPRESSION_FILE'])

    # inject only json
    META_DIR = Path(app.config['USER_DATA']) / app.config['META_DIR']

    inject_documents(new_index,
                    app.config['USER_DATA'],
                    dst_path = app.config['DST_DIR'],
                    json_path = app.config['JSON_DIR'],
                    meta_path = META_DIR,
                    sections=sections)

    # Switch index in alias
    put_alias(new_index, index_name)
    delete_alias(old_index, index_name)

    return make_response({'color': new_index}, 200)

@admin_bp.route('/threshold', methods=['PUT'])
def threshold():
    """ Save display or relevance thresholds
    Returns: Usual HTTP status codes
        201: Update
        500: Server abort
    """

    body = request.get_json(force=True)
    d_threshold = body.get('d_threshold', None)
    r_threshold = body.get('r_threshold', None)

    threshold_file = Path(app.config['USER_DATA']) / app.config['THRESHOLD_FILE']

    if threshold_file.exists() and (d_threshold is not None and r_threshold is not None):
        # insert new thresholds
        body["d_threshold"] = int(d_threshold)
        body["r_threshold"] = r_threshold
        with open(threshold_file, "w+") as jsonFile:
            json.dump(body, jsonFile)

        return make_response(jsonify(sucess=True), 201)
    else:
        return abort(500)



@admin_bp.route("/synonym/<int:key>", methods=["DELETE", "PUT"])
def synonym(key:int):
    """ Add, replace or delete a synonym in its file. If a creation, append
        at the beginning.
    Args:
        key (int): The row number of the synonym in the synonym file
    Returns: Usual HTTP status codes
        204: Delete
        200: Create
        201: Update
        202: Row already saved
        500: Server abort
    """
    filename = request.args.get('filename', app.config['GLOSSARY_FILE'])
    synonym_file = Path(app.config['USER_DATA']) / (filename + '.txt')
    if 'glossaire' in filename:
        names = ['expressionB','expressionA']
        sep = ' => '
    elif 'expression' in filename:
        names = ['expressionA']
        sep = ';'
    else:
        return abort(501)

    if synonym_file.exists():
        synonym_df = pd.read_csv(synonym_file, header=None, sep=sep, names=names)
        synonym_df['key'] = synonym_df.index + 1

    else:
        return abort(503)

    if request.method == 'PUT':
        body = request.get_json(force=True)
        if any([name not in body for name in names]):
            print('Missing keys')
            return  abort(500)
        else:
            if 'glossaire' in filename:
                list_token = clean(body['expressionB'], app.config['INDEX_NAME'])
                body['expressionB'] = ' '.join(list_token)
                if '_' not in body['expressionA']:
                    body['expressionA'] = '_' + body['expressionA'].upper() + '_'

            elif 'expression' in filename:
                list_token = clean(body['expressionA'], app.config['INDEX_NAME'])
                body['expressionA'] = ' '.join(list_token).upper()
            else:
                return abort(501)

        # test if entry exists
        match_df = pd.Series(True, index=synonym_df.index)
        for name in names:
            match_df = match_df & (synonym_df[name] == body[name])
        if match_df.any():
            status = 202 # do nothing

        elif key in synonym_df['key'].tolist():
            status = 200 # update
            # assign body value to dataframe
            for name in names:
                synonym_df.loc[synonym_df['key'] == key, name] = body[name]

        else:
            body.update({'key': key})
            status = 201 # create
            synonym_df = pd.concat([pd.DataFrame(body,index=[0]),
                                    synonym_df], ignore_index=True)

    elif request.method == 'DELETE':
        if key in synonym_df['key'].tolist():
            status = 200
            synonym_df = synonym_df[synonym_df['key'] != key]
        else:
            status = 404
    #import pdb; pdb.set_trace()
    #synonym_df.to_csv(synonym_file, sep=str('=>'), header=False, index=False, encoding='utf-8')
    synonym_df['key'] = range(len(synonym_df))
    synonym_df['key'] += 1
    if 'glossaire' in filename:
        synonym_file.write_text('\n'.join((synonym_df['expressionB'] + ' => ' + synonym_df['expressionA']).tolist()))
        return make_response(synonym_df.to_json(orient='records'), status)

    elif 'expression' in filename:
        synonym_file.write_text('\n'.join((synonym_df['expressionA']).tolist()))
        return make_response(synonym_df.to_json(orient='records'), status)
