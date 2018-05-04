#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `yamlsql` package."""

import pytest

from yamlsql import logic

from fixtures import conn_id

### Test Logic

def test_list_tables(conn_id):
    result = logic.list_tables(conn_id)
    assert result[0] == {'name': 'public.test_user', 'type': 'table'}
    assert result[1] == {'name': 'public.test_user_view', 'type': 'view'}

def test_describe_table(conn_id):
    result = logic.describe_table(conn_id, 'test_user')
    assert result == [
        {'field': 'id', 'type': 'integer'},
        {'field': 'name', 'type': 'text'},
        {'field': 'email', 'type': 'text'},
        {'field': 'password', 'type': 'text'},
        ]

### Test Emacs
