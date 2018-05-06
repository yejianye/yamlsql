import sqlparse
from funcy import omit, merge
from ruamel.yaml.comments import CommentedMap

from .parser import YAMLParser


def sql_format(sql):
    sql = sql.strip()
    if not sql.endswith(';'):
        sql = sql + ';'
    return sqlparse.format(sql.strip(), reindent=True, keyword_case='upper')


def _build_clause(name, item):
    key = name.replace(' ', '_')
    if key not in item:
        return ''
    return '{} {}'.format(name, ','.join(item[key]))


class Processor(object):
    when = None

    def process(self, item):
        if self.can_apply(item):
            return self.transform(item)
        return item

    def transform(self, item):
        raise NotImplemented()

    def can_apply(self, item):
        if self.when:
            return self.when in item
        return True


class SqlProcessor(Processor):
    when = 'sql'

    def transform(self, item):
        return sql_format(item['sql'])


class SelectProcessor(Processor):
    when = 'select'
    tmpl = """
    select {fields} from {from_}
    {when}
    {group_by}
    {order_by}
    {limit}
    """

    def transform(self, item):
        ctx = dict(
            fields=','.join(item['select']),
            from_=item['from'],
            when=_build_clause('when', item),
            group_by=_build_clause('group by', item),
            order_by=_build_clause('order by', item),
            limit=_build_clause('limit', item))
        sql = self.tmpl.format(**ctx).strip()
        return merge(
            omit(item, ['select', 'from', 'group_by', 'order_by', 'limit']),
            {'sql': sql})


class SQLRender(object):
    MAX_ITERATION = 100
    DEFAULT_PROCESSORS = [SqlProcessor, SelectProcessor]

    def __init__(self, content, processors=DEFAULT_PROCESSORS):
        self.parser = YAMLParser(content)
        if not processors:
            processors = self.DEFAULT_PROCESSORS
        self.processors = [cls() for cls in processors]

    def render(self, query_name=None, lineno=None):
        """ Render YAML to SQL
        If `query_name` is specified, only render query with specified name
        If `lineno` is specified, only render query around specified line
        """
        if query_name:
            items = [item for item in self.parser.doc
                     if item.get('name') == query_name]
            return '\n\n'.join(self.render_item(item) for item in items)

        if lineno:
            return self.render_item(self.parser.find_root(lineno))

        return '\n\n'.join(self.render_item(item) for item in self.parser.doc)

    def render_item(self, item):
        for i in xrange(self.MAX_ITERATION):
            for p in self.processors:
                if isinstance(item, basestring):
                    return item
                if isinstance(item, CommentedMap):
                    item = dict(item)
                item = p.process(item)

        raise Exception(
            "Cannot parse the item within {} iterations:\n{}".format(
                self.MAX_ITERATION, item))
