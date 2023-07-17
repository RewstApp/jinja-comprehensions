import pytest
from pytest_lambda import lambda_fixture

from .base import BaseJinjaEvaluationTest

_BASE_SCALAR_COMPREHENSION_EXPRS = {
    'comp':
        '''i for i in range(10)''',
    'comp-cond':
        '''i for i in range(10) if i % 2 == 0''',
    'comp-tuple-iter':
        '''a + b for a, b in [(0, 1), (2, 3)]''',
    'comp-multi-level':
        '''n for l in [(0, 1), (2, 3)] for n in l''',
    'comp-multi-level-cond':
        '''n
            for l in [(0,), (1, 2), (3, 4, 5), (6, 7, 8, 9)]
            if l.__len__() % 2 == 1
            for n in l
            if n % 2 == 0''',
}
_BASE_SCALAR_COLLECTION_EXPRS = {
    'scalar':
        '''1337''',
    'dynamic-scalar':
        '''max((0, 1337))''',
    **_BASE_SCALAR_COMPREHENSION_EXPRS,
}
LIST_COMPREHENSION_EXPRS = {
    'list-' + k: f'[{v}]'
    for k, v in _BASE_SCALAR_COLLECTION_EXPRS.items()
}
SET_COMPREHENSION_EXPRS = {
    'set-' + k: '{%s}' % v
    for k, v in _BASE_SCALAR_COLLECTION_EXPRS.items()
}
PARENTHESIZED_GENERATOR_EXPRS = {
    'gen-single-arg-' + k: f'list(({v}))'
    for k, v in _BASE_SCALAR_COMPREHENSION_EXPRS.items()
}
SINGLE_ARG_GENERATOR_EXPRS = {
    'gen-parens-' + k: f'list({v})'
    for k, v in _BASE_SCALAR_COMPREHENSION_EXPRS.items()
}
DICT_COMPREHENSION_EXPRS = {
    'dict-comp':
        '''{"i"*i: i*10 for i in range(10)}''',
    'dict-comp-cond':
        '''{"i"*i: i*10 for i in range(10) if i % 2 == 0}''',
    'dict-comp-tuple-iter':
        '''{k: v + 's' for k, v in dict(apple='apple', pear='pear').items()}''',
    'dict-comp-multi-level':
        '''{word + i.__str__(): c for word in ['apple', 'butt'] for i, c in enumerate(word)}''',
    'dict-comp-multi-level-cond':
        '''{word + i.__str__(): c
            for word in ['apple', 'butt', 'fart']
            if not word.startswith('a')
            for i, c in enumerate(word)
            if i % 2 == 1}
        ''',
}
COMPREHENSION_EXPRS: dict[str, str] = {
    **LIST_COMPREHENSION_EXPRS,
    **SET_COMPREHENSION_EXPRS,
    **PARENTHESIZED_GENERATOR_EXPRS,
    **SINGLE_ARG_GENERATOR_EXPRS,
    **DICT_COMPREHENSION_EXPRS,
}
COMPREHENSION_EXPRS = {k: v.replace('\n', '') for k, v in COMPREHENSION_EXPRS.items()}


class DescribeComprehensions(BaseJinjaEvaluationTest):
    expr = lambda_fixture(params=[
        pytest.param(expr, id=name)
        for name, expr in COMPREHENSION_EXPRS.items()
    ])
