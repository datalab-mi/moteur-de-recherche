from pathlib import Path
from dotenv import load_dotenv
import os, json
import pandas as pd
#Parsing argument
from .parser import parser

print('init')
args = parser.parse_args()

args.base_path = Path(args.base_path)
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
