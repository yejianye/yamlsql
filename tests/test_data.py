import random

from sqlalchemy import create_engine
import pandas as pd

def gen_row():
    return {
        'gender': random.choice(['female', 'male']),
        'age': random.randint(10, 80),
        'height': 100 + random.random() * 100
    }

def main():
    size = 1000
    table_name = 'test_data'

    df = pd.DataFrame([gen_row() for _ in xrange(size)])
    print df.head()
    conn = create_engine('postgresql://ryan@localhost:5432/yamlsql-test')
    df.to_sql(table_name, con=conn, if_exists='replace')

if __name__ == '__main__':
    main()
