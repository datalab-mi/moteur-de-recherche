import sys, json, os, time
from pathlib import Path  # python3 only
from dotenv import load_dotenv
from os import environ
import pandas as pd
import elasticsearch
from elasticsearch import Elasticsearch
import pytest
from argparse import Namespace
from benchmark.sentence_transformers import main

env_path = '/app/benchmark/bld'


def test_main():
    args = Namespace(
            base_path=env_path, # optional, take current
            qr_path="QR_file.ods",
            dotenv_path=".env-bld",
            metric='dcg',
            index=True)
    result = main(args)

#     assert result['metric_score'] == 1
