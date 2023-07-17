import pytest
from pytest_lambda import lambda_fixture

from tests.base import BaseJinjaEvaluationTest

_SCALAR_COLLECTION_EXPRS = {
    'empty':
        '''''',
    'single':
        '''1''',
    'multiple':
        '''1, 2, 3''',
    'multiple-dupes':
        '''1, 2, 3, 1, 2, 3''',
    'spread':
        '''1, *range(2, 4), 5''',
    'multiple-spread':
        '''1, *range(2, 4), 5, *range(6, 8), 9''',
}
_DICT_COLLECTION_EXPRS = {
    'dict-empty':
        '''{}''',
    'dict-single':
        '''{'a': 1}''',
    'dict-multiple':
        '''{'a': 1, 'b': 2, 'c': 3}''',
    'dict-multiple-dupes':
        '''{'a': 1, 'b': 2, 'c': 3, 'a': 1, 'b': 2, 'c': 3}''',
    'dict-spread':
        '''{'a': 1, **{'b': 2, 'c': 3}, 'd': 4}''',
    'dict-multiple-spread':
        '''{'a': 1, **{'b': 2, 'c': 3}, 'd': 4, **{'e': 5, 'f': 6}, 'g': 7}''',
    'dict-spread-dynamic':
        '''{'a': 1, **{'k%s' % i: i for i in range(2, 4)}, 'd': 4}''',
    'dict-multiple-spread-dynamic':
        '''{'a': 1,
            **{'k%s' % i: i for i in range(2, 4)},
            'd': 4,
            **{'k%s' % i: i for i in range(5, 7)},
            'g': 7,
           }
        ''',
}

_LIST_LITERAL_EXPRS = {
    'list-' + name: '[%s]' % expr
    for name, expr in _SCALAR_COLLECTION_EXPRS.items()
}
_TUPLE_LITERAL_EXPRS = {
    'tuple-' + name: '(%s)' % expr
    for name, expr in _SCALAR_COLLECTION_EXPRS.items()
}
_SET_LITERAL_EXPRS = {
    'set-' + name: '{%s}' % expr
    for name, expr in _SCALAR_COLLECTION_EXPRS.items()
}

COLLECTION_LITERAL_EXPRS = {
    **_LIST_LITERAL_EXPRS,
    **_TUPLE_LITERAL_EXPRS,
    **_SET_LITERAL_EXPRS,
    **_DICT_COLLECTION_EXPRS,
}
COLLECTION_LITERAL_EXPRS = {k: v.replace('\n', '') for k, v in COLLECTION_LITERAL_EXPRS.items()}


class DescribeCollectionLiterals(BaseJinjaEvaluationTest):
    expr = lambda_fixture(params=[
        pytest.param(expr, id=name)
        for name, expr in COLLECTION_LITERAL_EXPRS.items()
    ])
