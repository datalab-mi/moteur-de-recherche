"""App configuration."""
from os import environ, getenv
import os
from dotenv import load_dotenv
from pathlib import Path


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

    FLASK_ENV = getenv('FLASK_ENV','debug')
    # TODO: Remove env_path dependency, pass it to docker-compose as env-file.
    #env_path = '/app/tests/iga/.env-iga'

    print("USER_DATA : " + os.getenv('USER_DATA'))
    
    USER_DATA = getenv('USER_DATA')
    INDEX_NAME = getenv('INDEX_NAME')
    ES_DATA = getenv('ES_DATA')
    MAPPING_FILE = getenv('MAPPING_FILE')
    GLOSSARY_FILE = getenv('GLOSSARY_FILE')
    EXPRESSION_FILE = getenv('EXPRESSION_FILE')
    RAW_EXPRESSION_FILE = getenv('RAW_EXPRESSION_FILE')

    PDF_DIR = getenv('PDF_DIR')
    ODT_DIR = getenv('ODT_DIR')

    JSON_DIR = getenv('JSON_DIR')
    META_DIR = getenv('META_DIR')


    print('Read config')
    pass
