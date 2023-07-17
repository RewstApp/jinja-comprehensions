from typing import Callable, Any

import jinja2
import jinja2.compiler
import pytest
from pytest_lambda import not_implemented_fixture, lambda_fixture


class BaseJinjaEvaluationTest:
    expr = not_implemented_fixture()
    source = lambda_fixture(lambda expr: '{{ %s }}' % expr)

    def _do_test(
        self,
        jinja_env: jinja2.Environment,
        preprocess_expected: Callable[[Any], Any],
        expr: str,
        actual: Any,
    ):
        expected = preprocess_expected(eval(expr))
        try:
            assert expected == actual
        except AssertionError:
            # Collect some useful troubleshooting info
            tmpl_node = jinja_env.parse(self.source)
            tmpl_source = jinja2.compiler.generate(tmpl_node, jinja_env, None, None)
            raise

    @pytest.mark.asyncio
    async def it_async_evaluates_jinja_exactly_as_python_does(
        self, source, expr, async_env, preprocess_expected
    ):
        template = async_env.from_string(source)
        actual = await template.render_async()
        self._do_test(async_env, preprocess_expected, expr, actual)

    @pytest.mark.asyncio
    async def it_evaluates_jinja_exactly_as_python_does(
        self, source, expr, sync_env, preprocess_expected
    ):
        template = sync_env.from_string(source)
        actual = template.render()
        self._do_test(sync_env, preprocess_expected, expr, actual)
