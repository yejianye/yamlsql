import pytest

from yamlsql.logic import DBMeta

@pytest.fixture()
def db_meta():
    return DBMeta.create_instance("postgresql://ryan@localhost:5432/yamlsql-test")
