from typing import TypeVar

import asyncstdlib
import jinja2.nativetypes
import pytest
from pytest_lambda import lambda_fixture, static_fixture

from jinja_comprehensions import (
    ComprehensionEnvironment,
    NativeComprehensionEnvironment,
    NoLiteralEvalComprehensionNativeEnvironment,
)

EnvType = TypeVar('EnvType', bound=jinja2.Environment)

# Ensure our base test class gets its assertions rewritten
pytest_plugins = ['tests.base']


env_kwargs = static_fixture(dict(
    undefined=jinja2.StrictUndefined,
))

env_class = lambda_fixture(params=[
    pytest.param(ComprehensionEnvironment, id='normal'),
    pytest.param(NativeComprehensionEnvironment, id='native'),
    pytest.param(NoLiteralEvalComprehensionNativeEnvironment, id='native-no_literal_eval'),
])

is_native_env = lambda_fixture(
    lambda env_class: issubclass(env_class, jinja2.nativetypes.NativeEnvironment)
)

preprocess_expected = lambda_fixture(
    lambda is_native_env: (lambda o: o) if is_native_env else str
)

sync_env = lambda_fixture(
    lambda env_kwargs, env_class, add_env_globals: (
        add_env_globals(env_class(**env_kwargs))
    )
)

async_env = lambda_fixture(
    lambda env_kwargs, env_class, add_env_globals: (
        add_env_globals(env_class(**env_kwargs, enable_async=True))
    )
)

sync_globals = static_fixture(dict(
    list=list,
    tuple=tuple,
    set=set,
    dict=dict,
    min=min,
    max=max,
    enumerate=enumerate,
))

async_globals = static_fixture(dict(
    list=asyncstdlib.list,
    tuple=asyncstdlib.tuple,
    set=asyncstdlib.set,
    dict=asyncstdlib.dict,
    min=asyncstdlib.min,
    max=asyncstdlib.max,
    enumerate=asyncstdlib.enumerate,
))


@pytest.fixture
def add_env_globals(async_globals, sync_globals):
    def _init_env_globals(env: EnvType) -> EnvType:
        env.globals.update(async_globals if env.is_async else sync_globals)
        return env
    return _init_env_globals
