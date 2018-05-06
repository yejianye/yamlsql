from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from funcy import print_calls


class YAMLParser(object):
    def __init__(self, content):
        yaml = YAML()
        self._doc = yaml.load(content)

    @property
    def doc(self):
        """ Return parsed doccument """
        return self._doc

    def find_obj(self, lineno):
        """ Find the most inner object contains specific line """
        path = self.find_path(lineno)
        return self.find_obj_from_path(path)

    def find_root(self, lineno):
        """ Find root object contains specific line """
        path = self.find_path(lineno, level=1)
        return self.find_obj_from_path(path)

    def find_parent(self, lineno):
        """ Find parent object contains specific line """
        path = self.find_path(lineno)
        return self.find_obj_from_path(path[:-1])

    def find_path(self, lineno, level=None):
        """ Return the path from root object to most inner object contains
        specific line. The path is a list of array index or dict key.

        If level is not None, only return the first n-th elements in the path.
        In order for the API to be more friendly with text editors,
        `lineno` starts with 1, not 0.
        """
        return self._find_path(self._doc, lineno - 1, level)

    def _find_path(self, root, lineno, level=None):
        if level == 0 or not isinstance(root, (CommentedMap, CommentedSeq)):
            return []
        items = [{'key': k, 'lineno': v[0]} for k, v in root.lc.data.items()]
        items.sort(key=lambda x: x['lineno'])
        key = None
        for i, item in enumerate(items):
            if item['lineno'] > lineno:
                key = items[i-1]['key']
                break
        if key is None:
            key = items[-1]['key']
        level = None if level is None else level - 1
        return [key] + self._find_path(root[key], lineno, level)

    def find_obj_from_path(self, path):
        """ Return the object from a index/key path. """
        item = self._doc
        while path:
            item = item[path[0]]
            path = path[1:]
        return item
