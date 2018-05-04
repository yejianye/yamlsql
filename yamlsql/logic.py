from pprint import pprint
from threading import Lock

from funcy import memoize, decorator
from sqlalchemy import text

from . import errors


SQL_FETCH_METADATA = text("""
select
  table_schema, table_name, column_name, data_type
from
  information_schema.columns
where
 table_schema not in ('information_schema', 'pg_catalog')
order by
 table_schema, table_name, ordinal_position
""")

SQL_LIST_TABLES = text("""
select
  schemaname, tablename
from
  pg_catalog.pg_tables
where
 schemaname not in ('information_schema', 'pg_catalog')
""")

SQL_LIST_VIEWS = text("""
select
  schemaname, viewname
from
  pg_catalog.pg_views
where
  schemaname not in ('information_schema', 'pg_catalog')
""")

SQL_DESCRIBE_TABLE = text("""
select
  column_name, data_type
from
  INFORMATION_SCHEMA.COLUMNS
where
  table_name = :name and
  table_schema = ANY(:schemas)
order by
  ordinal_position;
""")

@decorator
def require_metadata(func):
    func._args[0].fetch_metadata()
    return func()

class DBMeta(object):
    _instances = {}
    def __init__(self, conn_str, search_path=None):
        self.conn_str = conn_str
        self.search_path = search_path or ['public']
        self.conn_id = md5(conn_string).hexdigest()
        self.conn = self.connect()
        self._meta_lock = Lock()
        self._meta = None
        self._tables = None

    def connect(self):
        conn = create_engine(self.conn_str)
        conn.execute("set search_path to {};".format(','.join(self.search_path)))
        return conn

    def fetch_metadata(self):
        with self._meta_lock:
            if not self._meta:
                return
            meta_data = conn.execute(SQL_FETCH_METADATA):
            self._meta = {}
            for r in meta_data:
                table_name = "{}.{}".format(r['table_schema'], r['table_name'])
                table = self._meta.setdefault(table_name, {'fields': []})
                table['fields'].append(
                    {'field':r['column_name'], 'type': r['data_type']}
                )
            self._tables = self._meta.keys()
            self._tables.sort()

    @require_metadata
    def list_tables(self):
        return self._tables

    @require_metadata
    def describe_table(self, name):
        if name not in self._meta:
            raise errors.TableNotExist(name)
        return self._tables[name]['fields']

    def describe_field(self, table_name, field_name):
        pass

    @classmethod
    def get_instance(cls, conn_id):
        return cls._instances.get(conn_id)

    @classmethod
    def create_instance(cls, conn_str, search_path=None):
        db_meta = DBMeta(conn_str, search_path)
        cls._instances[db_meta.conn_id] = db_meta
        return db_meta.conn_id

@memoize
def list_tables(conn_id, include_views=True):
    """ List Tables and Views """
    conn = get_conn(conn_id)
    tables = conn.execute(SQL_LIST_TABLES)
    result = [{
        "name": "{}.{}".format(r['schemaname'], r['tablename']),
        "type": "table"
        } for r in tables]

    if include_views:
        views = conn.execute(SQL_LIST_VIEWS)
        views = [{
            "name": "{}.{}".format(r['schemaname'], r['viewname']),
            "type": "view"
            } for r in views]
        result += views

    result.sort(key=lambda x: x['name'])
    return result

def _parse_table_name(conn_id, name):
    schemas = get_search_path(conn_id)
    if '.' in name:
        schema, name = name.split('.')
        schemas = [schema]
    return schemas, name

def describe_table(conn_id, table_name):
    """ Describe a table and its columns """
    schemas, name = _parse_table_name(conn_id, table_name)
    result = get_conn(conn_id).execute(SQL_DESCRIBE_TABLE,
                                       name=name, schemas=schemas)
    if result.rowcount == 0:
        return None
    return [{'field': r['column_name'],
             'type': r['data_type']} for r in result]
