"""App configuration."""
from os import environ, getenv
from dotenv import load_dotenv



class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    """
    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_ENV = environ.get('FLASK_ENV')

    # Flask-Assets
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Static Assets
    STATIC_FOLDER = environ.get('STATIC_FOLDER')
    TEMPLATES_FOLDER = environ.get('TEMPLATES_FOLDER')
    COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')

    """
    env_path = '/app/tests/iga/.env-iga'
    load_dotenv(dotenv_path=env_path)
    USER_DATA = getenv('USER_DATA')
    NOM_INDEX = getenv('NOM_INDEX')
    ES_DATA = getenv('ES_DATA')
    MAPPING_FILE = getenv('MAPPING_FILE')
    GLOSSARY_FILE = getenv('GLOSSARY_FILE')
    EXPRESSION_FILE = getenv('EXPRESSION_FILE')
    PDF_DIR = getenv('PDF_DIR')
    JSON_DIR = getenv('JSON_DIR')
    print('Read config')
    pass
