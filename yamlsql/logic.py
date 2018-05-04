from hashlib import md5
from threading import Lock

from funcy import decorator
from sqlalchemy import text, create_engine

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


@decorator
def require_metadata(func):
    func._args[0].fetch_metadata()
    return func()


class DBMeta(object):
    _instances = {}

    def __init__(self, conn_str, search_path=None):
        self.conn_str = conn_str
        self.search_path = search_path or ['public']
        self.conn_id = md5(conn_str).hexdigest()
        self.conn = self.connect()
        self._meta_lock = Lock()
        self._meta = None
        self._tables = None

    def connect(self):
        conn = create_engine(self.conn_str)
        conn.execute("set search_path to {};".format(
            ','.join(self.search_path))
        )
        return conn

    def fetch_metadata(self):
        with self._meta_lock:
            if self._meta:
                return
            meta_data = self.conn.execute(SQL_FETCH_METADATA)
            self._meta = {}
            for r in meta_data:
                table_name = "{}.{}".format(r['table_schema'], r['table_name'])
                table = self._meta.setdefault(table_name, {'fields': []})
                table['fields'].append(
                    {'field': r['column_name'], 'type': r['data_type']}
                )
            self._tables = self._meta.keys()
            self._tables.sort()

    @require_metadata
    def list_tables(self):
        return self._tables

    def _find_table(self, name):
        if '.' in name:
            candidates = [name]
        else:
            candidates = ['{}.{}'.format(s, name) for s in self.search_path]

        for cname in candidates:
            if cname in self._meta:
                return cname
        raise errors.TableNotFound(name)

    @require_metadata
    def describe_table(self, name):
        name = self._find_table(name)
        return self._meta[name]['fields']

    def describe_field(self, table_name, field_name):
        pass

    @classmethod
    def get_instance(cls, conn_id):
        return cls._instances.get(conn_id)

    @classmethod
    def create_instance(cls, conn_str, search_path=None):
        db_meta = DBMeta(conn_str, search_path)
        cls._instances[db_meta.conn_id] = db_meta
        return db_meta
