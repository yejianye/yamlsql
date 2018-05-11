import os
import json
import urllib

import pytest

from yamlsql.server import app

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def json_post(client, url, params):
    resp = client.post(url, data = json.dumps(params),
                       headers={'Content-Type': 'application/json'})
    return json.loads(resp.data)

def json_get(client, url, params):
    if params:
        url = "{}?{}".format(url, urllib.urlencode(params))
    resp = client.get(url)
    return json.loads(resp.data)

@pytest.fixture
def client():
    return app.test_client()

@pytest.fixture
def conn_id(client):
    result = json_post(client, '/connect', {
        "conn_string": "postgresql://ryan@localhost:5432/yamlsql-test",
        })
    return result['data']['conn_id']

@pytest.fixture
def content():
    path = os.path.join(DATA_DIR, 'simple.yaml')
    return open(path).read()

def test_api_list_table(client, conn_id):
    result = json_get(client, '/list_tables', {
        'conn_id': conn_id
        })
    assert result['data']['tables'] == [
        'public.test_data',
        'public.test_user',
        'public.test_user_view'
        ]

def test_api_describe_table(client, conn_id):
    result = json_get(client, '/describe_table', {
        'conn_id': conn_id,
        'name': 'public.test_user'
        })
    assert result['data']['type'] == 'table'
    assert result['data']['fields'] == [
        {'field': 'id', 'type': 'integer'},
        {'field': 'name', 'type': 'text'},
        {'field': 'email', 'type': 'text'},
        {'field': 'password', 'type': 'text'}
        ]

def test_api_describe_field(client, conn_id):
    result = json_get(client, '/describe_field', {
        'conn_id': conn_id,
        'table': 'public.test_data',
        'field': 'age'
        })
    age = result['data']
    assert age['min'] == 10 and age['max'] == 80

def test_api_run_sql(client, conn_id, content):
    params = {
        'conn_id': conn_id,
        'content': content,
        'lineno': 5,
        'limit': 50
        }
    result = json_post(client, '/run_sql', params)
    data = result['data']
    assert data['rowcount'] == 1000
    assert len(data['rows']) == 50
