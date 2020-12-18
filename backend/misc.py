# convert glossary from toufik to the new format
import requests
import argparse
from pathlib import Path
import pandas as pd
import json
#Parsing argument
parser = argparse.ArgumentParser(description='Evaluation of the metrics')
parser.add_argument('-src-file', type=str,
    help='file to convert')
parser.add_argument('-dst-file', type=str,
    help='file converted')
parser.add_argument('-filename', type=str,
    help='type of filename')


"""
example:
python3 backend/misc.py -filename glossaire -src-file /home/victor/Downloads/search/searchIGPN/Search_Engine_IGPN/Dash/Dictionnaire/Glossaire/Glossaire.txt -dst-file glossaire.txt
python3 backend/misc.py -filename raw_expression -src-file /home/victor/Downloads/search/searchIGPN/Search_Engine_IGPN/Dash/Dictionnaire/Glossaire/expressions_metier_enregistre.txt -dst-file raw_expression.txt

"""
def parser_glossaire(row):
    sep = " => "
    expressionA, expressionB = row.split(sep)
    print(expressionA + sep + expressionB)
    expressionB = " ".join(expressionB.split(", ")[1:])
    expressionA = expressionA.replace('.','')
    return expressionA, expressionB

def parser_expression(row):
    return row, None

def main(args):
    print(args)
    src_file = Path(args.src_file)
    dst_file = Path(args.dst_file)

    if not src_file.is_file():
        print("file not exist")
        exit(1)
    if src_file.suffix  not in [".csv", ".txt"]:
        print("file format is not a csv")
        exit(1)

    src_file_df = pd.read_fwf(src_file, encoding= 'utf-8',  header=None)
    for index, row in src_file_df.iterrows():
        print(10*"-")
        if 'glossaire' in args.filename:
            expressionA, expressionB = parser_glossaire(row.values[0])
        elif 'expression' in args.filename:
            expressionA, expressionB = parser_expression(row.values[0])

        print(expressionA, expressionB)
        body = {"expressionA":expressionA,"expressionB":expressionB}
        req = requests.put(
            'http://localhost/api/admin/synonym/{key}?filename={filename}'.format(
            key=0,
            filename=args.filename),
            data = json.dumps(body)
        )
        print(req.url)
        print(req.text)
if __name__ == '__main__':

    args = parser.parse_args()
    main(args)
