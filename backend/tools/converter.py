"""Fichier permettant de convertir les fichiers du .odt, pdf à .json """

import os
import json, collections
from odf import text, teletype
from odf.opendocument import load
from tika import parser
from os import environ
import re
from pathlib import Path
import unidecode

def normalize(string: str):
    """Strip lower and accent removal
    """
    return unidecode.unidecode(string.strip().lower())

def odt2json(path: str, sections: list = []) -> dict:
    """ Fonction qui permet la conversion des Json en Odt elle prend en argument:

    Args:
        path : le chemin du fichier en question
    Returns:
        text: text
    """

    sections = [{'key':normalize(x['key']), 'array':x['array']} for x in sections]

    print('Sections are : ')
    print(sections)
    # extract test from doc
    doc = load(path)
    L = [teletype.extractText(x) for x in doc.getElementsByType(text.P)]

    # remove None and empty string (i.e borders)
    L = [x for x in L if x and x != '']

    # replace \xa0 and \n
    L = [x.replace(u'\xa0', u' ').replace(u'\n' , u' ') for x in L]

    L2 = []

    for x in L:
        g = re.match("^({sections})\s*:\s*(.*)".format(sections='|'.join([x['key'] for x in sections] )), normalize(x))

        if g:
            L2 += [g.group(1), x[g.span(2)[0]: g.span(2)[1]]] # span rather group to get origal string
        else:
            # Section is not present
            L2 += [x]

    # Remove empty or digit element
    L2 = [x for x in L2 if x and x != '' and not x.isdigit()]

    data = {}
    section_content = []
    current_section = ''
    #import pdb; pdb.set_trace()

    for x in L2:
        if normalize(x) in [x['key'] for x in sections]:
            current_section = normalize(x)
            section_content = []
        else:
            section_content += [x]

        if current_section in [x['key'] for x in sections] :
            is_array = [x['array'] for x in sections if x['key'] == current_section][0]
            if is_array:
                data[current_section] = section_content
            else :
                data[current_section] = ' ,'.join(section_content)

    if '' in data:
        data.pop('')
    return data


def pdf2json(path: str, sections: list = []) -> dict:
    """
    Fonction qui permet la conversion des Pdf en json et prend en argument:
    Les sections du document ne sont pas encore supportées.
    Args:
        path : le chemin du fichier en question
    Returns:
        path: clean text
    """
    try:
        file_data = parser.from_file(path,"http://tika:9998/")
        data = file_data['content']
        data = data.replace(u'\xa0', u' ')
        data = data.replace(u'\n' , u' ')
        data = data.replace(u'\xa0', u' ')
        data = data.replace(u'\n' , u' ')
        data = re.sub(' +', ' ', data)
        data = data.strip()

    except Exception as e:
        print(e)
        data = ""
    return {"content" : data}

def save_json(data, json_file: str):
    json_file = Path(json_file)
    if not json_file.parent.exists():
        json_file.parent.mkdir(parents=True, exist_ok=True)
    print("save json to %s"%json_file)
    with open(json_file , 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return 'OK'

if __name__ == '__main__':
    path = '/app/tests/doc.odt'
    data = convertisseur_odt_txt(path)
    save_json(data, 'docOdt.json')

    path = '/app/tests/doc.pdf'
    txt = convertisseur_pdf_txt(path)
    name = 'doc name'
    Titre = 'doc titre'
    Date = 'doc date'
    Auteurs = 'doc auteur 1'
    data = dict(Titre=Titre, Date=Date,Auteurs=Auteurs)
    data['Corps'] = txt
    save_json(data, 'doc.json')
