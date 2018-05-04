from hashlib import md5

from sqlalchemy import create_engine

CONN_MAP = {}

def create_conn(conn_string, search_path=None):
    conn_id = md5(conn_string).hexdigest()
    conn = create_engine(conn_string)
    search_path = search_path or ['public']
    CONN_MAP[conn_id] = {
        "conn_obj": conn,
        "conn_string": conn_string,
        "search_path": search_path
    }
    conn.execute("set search_path to {};".format(','.join(search_path)))
    return conn_id

def get_conn(conn_id):
    if conn_id not in CONN_MAP:
        raise Exception("Invalid Connection: {}".format(conn_id))
    return CONN_MAP[conn_id]['conn_obj']

def get_search_path(conn_id):
    if conn_id not in CONN_MAP:
        raise Exception("Invalid Connection: {}".format(conn_id))
    return CONN_MAP[conn_id]['search_path']

def reconnect(conn_id):
    pass
