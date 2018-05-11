#!/usr/bin/env python

from flask import Flask

from yamlsql.dbmeta import DBMeta
from yamlsql.render import SQLRender
from yamlsql import emacs
from yamlsql.base import api_request, emacs_converter

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
    db = DBMeta.create_instance(conn_string, search_path)
    db.fetch_metadata()
    return {"conn_id": db.conn_id}

@app.route('/list_tables',  methods=['GET'])
@api_request
def list_tables(conn_id):
    db = DBMeta.get_instance(conn_id)
    return {'tables': db.list_tables()}


@app.route('/describe_table',  methods=['GET'])
@api_request
@emacs_converter(emacs.describe_table)
def describe_table(conn_id, name):
    db = DBMeta.get_instance(conn_id)
    fields = db.describe_table(name)
    if not fields:
        raise Exception('Cannot find table or view named {}'.format(name))
    return {
        'type': 'table',
        'fields': fields
        }

@app.route('/describe_field',  methods=['GET'])
@api_request
@emacs_converter(emacs.describe_field)
def describe_field(conn_id, table, field):
    db = DBMeta.get_instance(conn_id)
    result = db.describe_field(table, field)
    result['field_name'] = '{}.{}'.format(table, field)
    if not result:
        raise Exception('Cannot find field {}.{}'.format(table, field))
    return result

@app.route('/render_sql',  methods=['POST'])
@api_request
def render_sql(content, lineno=None):
    return {
        'sql': SQLRender(content).render(lineno=lineno)
        }

@app.route('/run_sql', methods=['POST'])
@api_request
def run_sql(conn_id, content, lineno=None, limit=100):
    db = DBMeta.get_instance(conn_id)
    sql = SQLRender(content).render(lineno=lineno)
    return db.run_sql(sql, limit=limit)
