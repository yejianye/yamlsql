from hashlib import md5
from threading import Lock

from funcy import decorator
from sqlalchemy import text, create_engine
from sqlalchemy.exc import ResourceClosedError

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

SQL_COUNT_DISTINCT = "select count(distinct {field_name}) from {table_name}"

SQL_MOST_COMMON = """
select {field_name}, count(*) as cnt from {table_name}
group by 1
order by 2 desc
limit {limit}
"""

SQL_NUMERIC_STATS = """
select
  min({field_name}) as min,
  max({field_name}) as max,
  avg({field_name}) as avg
from {table_name}
"""


@decorator
def require_metadata(func):
    func._args[0].fetch_metadata()
    return func()


def is_numeric(field):
    return field['type'] in (
        'bigint', 'integer', 'numeric', 'real', 'smallint',
        'double precision'
        )

def build_conn_id(conn_str):
    return md5(conn_str).hexdigest()

class DBMeta(object):
    _instances = {}

    def __init__(self, conn_str, search_path=None):
        self.conn_str = conn_str
        self.search_path = search_path or ['public']
        self.conn_id = build_conn_id(conn_str)
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

    @require_metadata
    def describe_field(self, table_name, field_name):
        table_name = self._find_table(table_name)
        field = [f for f in self._meta[table_name]['fields']
                 if f['field'] == field_name]
        if not field:
            raise errors.FieldNotFound(table_name, field_name)

        field = field[0]
        # is it categorical field?
        limit = 20
        sql_ctx = {
            'table_name': table_name,
            'field_name': field_name,
            'limit': limit
            }
        distinct_count = self.conn.execute(
            SQL_COUNT_DISTINCT.format(**sql_ctx)
        ).first()[0]
        most_common = self.conn.execute(SQL_MOST_COMMON.format(**sql_ctx))
        most_common = [{'value': r[field_name], 'count': r['cnt']}
                       for r in most_common]
        result = {
            'distinct_count': distinct_count,
            'most_common': most_common
            }

        if distinct_count > limit and is_numeric(field):
            stats = self.conn.execute(
                SQL_NUMERIC_STATS.format(**sql_ctx)
            ).first()
            result.update({
                'min': stats['min'],
                'max': stats['max'],
                'avg': stats['avg'],
                })
        return result

    def run_sql(self, sql, limit=100):
        rs = self.conn.execute(sql)
        result = {
            "rowcount": rs.rowcount
            }
        try:
            rows = rs.fetchmany(limit)
            if rows:
                result['columns'] = rows[0].keys()
                result['rows'] = [r.values() for r in rows]
        except ResourceClosedError:
            pass
        return result

    @classmethod
    def get_instance(cls, conn_id):
        return cls._instances.get(conn_id)

    @classmethod
    def create_instance(cls, conn_str, search_path=None):
        conn_id = build_conn_id(conn_str)
        if conn_id in cls._instances:
            return cls._instances[conn_id]
        db_meta = DBMeta(conn_str, search_path)
        cls._instances[db_meta.conn_id] = db_meta
        return db_meta
