#!/usr/bin/env python

from flask import Flask

from yamlsql import logic
from yamlsql import emacs
from yamlsql.base import api_request, emacs_converter
from yamlsql.connection import create_conn

app = Flask(__name__)


@app.route('/', methods=['GET'])
@api_request
def index():
    return {"text": "Server is running"}


@app.route('/connect', methods=['POST'])
@api_request
def connect(conn_string, search_path=None):
    if not search_path:
        search_path = ['public']
    conn_id = create_conn(conn_string, search_path)
    return {"conn_id": conn_id}


@app.route('/list_tables',  methods=['GET'])
@api_request
def list_tables(conn_id):
    return {'tables': logic.list_tables(conn_id)}


@app.route('/describe_table',  methods=['GET'])
@api_request
@emacs_converter(emacs.describe_table)
def describe_table(conn_id, name):
    fields = logic.describe_table(conn_id, name)
    if not fields:
        raise Exception('Cannot find table or view named {}'.format(name))
    return {
        'type': 'table',
        'fields': logic.describe_table(conn_id, name)
        }
