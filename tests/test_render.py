#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pprint import pprint

import pytest

from yamlsql.render import SQLRender, sql_format

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


@pytest.fixture
def simple_render():
    path = os.path.join(DATA_DIR, 'simple.yaml')
    return SQLRender(open(path).read())


def test_render_query_name(simple_render):
    sql = simple_render.render(query_name='query1')
    assert sql == sql_format("select * from public.test_data")


def test_render_lineno(simple_render):
    sql1 = sql_format("select * from public.test_data")
    sql2 = sql_format("select gender,age from public.test_data")
    assert simple_render.render(lineno=1) == sql1
    assert simple_render.render(lineno=5) == sql2


def test_render(simple_render):
    sql = simple_render.render()
    assert sql == sql_format(
        "select * from public.test_data;"
        "select gender,age from public.test_data;")
