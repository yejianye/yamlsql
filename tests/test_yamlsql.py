#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `yamlsql` package."""

import pytest

from yamlsql import logic

from fixtures import db_meta

### Test Logic

def test_list_tables(db_meta):
    result = db_meta.list_tables()
    assert result == ['public.test_user', 'public.test_user_view']

def test_describe_table(db_meta):
    result = db_meta.describe_table('test_user')
    assert result == [
        {'field': 'id', 'type': 'integer'},
        {'field': 'name', 'type': 'text'},
        {'field': 'email', 'type': 'text'},
        {'field': 'password', 'type': 'text'},
        ]

### Test Emacs
