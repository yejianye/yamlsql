#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint

from pytest import approx

from yamlsql import dbmeta
from fixtures import db_meta

def test_list_tables(db_meta):
    result = db_meta.list_tables()
    assert result == [
        'public.test_data',
        'public.test_user',
        'public.test_user_view']

def test_describe_table(db_meta):
    result = db_meta.describe_table('test_user')
    assert result == [
        {'field': 'id', 'type': 'integer'},
        {'field': 'name', 'type': 'text'},
        {'field': 'email', 'type': 'text'},
        {'field': 'password', 'type': 'text'}
        ]

def test_describe_field(db_meta):
    age = db_meta.describe_field('test_data', 'age')
    assert 44 < age['avg'] < 45
    assert age['min'] == 10
    assert age['max'] == 80
    assert age['distinct_count'] == 71
    assert age['most_common'][:5] == [
        {'count': 22L, 'value': 74L},
        {'count': 21L, 'value': 46L},
        {'count': 20L, 'value': 62L},
        {'count': 19L, 'value': 65L},
        {'count': 19L, 'value': 24L},
    ]

    gender = db_meta.describe_field('test_data', 'gender')
    assert gender['distinct_count'] == 2
    assert gender['most_common'] == [
        {'count': 503L, 'value': u'male'},
        {'count': 497L, 'value': u'female'}
    ]

    height = db_meta.describe_field('test_data', 'height')
    assert height['avg'] == approx(149.60, 0.1)
    assert height['min'] == approx(100.39, 0.1)
    assert height['max'] == approx(199.92, 0.1)
    assert height['distinct_count'] == 1000
