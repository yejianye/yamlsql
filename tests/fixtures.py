import pytest

from yamlsql.connection import create_conn

@pytest.fixture(scope='session')
def conn_id():
    return create_conn("postgresql://ryan@localhost:5432/yamlsql-test")
