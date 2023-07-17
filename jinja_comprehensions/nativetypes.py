from __future__ import annotations

from itertools import chain, islice
from types import GeneratorType
from typing import Any, Iterable

from jinja2.nativetypes import NativeCodeGenerator, NativeEnvironment, NativeTemplate

from jinja_comprehensions.compiler import AsyncOperandsCodeGenerator, ComprehensionCodeGenerator
from jinja_comprehensions.environment import ComprehensionEnvironment
from jinja_comprehensions.runtime import syncify_awaitable
from jinja_comprehensions.util import add_template_class, with_code_generator

__all__ = [
    'NativeComprehensionEnvironment',
    'NoLiteralEvalNativeEnvironment',
    'NoLiteralEvalComprehensionNativeEnvironment',
]


def no_literal_eval_native_concat(values: Iterable[Any]) -> Any | None:
    """Concatenate output values of a rendered template into result form

    By default, Jinja2's native_concat shoots values into `ast.literal_eval`. This means
    `123`, `{{ 123 }}`, and `{{ '123' }}` all end up as `native_concat(['123'])`, and
    all evaluate to the integer 123. An enormous caveat of this is that it's impossible
    to return a string consisting only of digits — it will always be literal_eval'd to
    an integer!

    This altered version of `native_concat` eschews the usage of `ast.literal_eval`,
    and instead relies on the code generator to appropriately return native types, where
    applicable.
    """
    head = list(islice(values, 2))

    if not head:
        return None

    if len(head) == 1:
        return head[0]
    else:
        if isinstance(values, GeneratorType):
            values = chain(head, values)
        return "".join([str(v) for v in values])


class NoAsyncConcatNativeTemplate(NativeTemplate):
    """NativeTemplate that awaits values in render_async before passing them to environment.concat

    By default, Jinja2's NativeTemplate.render_async passes all final output values
    directly to the environment's concat function. Even though these output values are
    sourced from an `async for`, the values themselves may be async, and the synchronous
    concat() cannot handle them. Thus, we must sync-flatten them all by awaiting them first.
    """

    async def render_async(self, *args: Any, **kwargs: Any) -> Any:
        if not self.environment.is_async:
            raise RuntimeError(
                "The environment was not created with async mode enabled."
            )

        ctx = self.new_context(dict(*args, **kwargs))

        try:
            return self.environment_class.concat([
                await syncify_awaitable(n)
                async for n in self.root_render_func(ctx)  # type: ignore
            ])
        except Exception:
            return self.environment.handle_exception()


class NativeComprehensionCodeGenerator(ComprehensionCodeGenerator, NativeCodeGenerator):
    pass


@add_template_class
class NativeComprehensionEnvironment(ComprehensionEnvironment, NativeEnvironment):
    code_generator_class = NativeComprehensionCodeGenerator
    template_class = NoAsyncConcatNativeTemplate


class NoLiteralEvalNativeCodeGenerator(NativeCodeGenerator):
    def _output_const_repr(self, group: Iterable[Any]) -> str:
        """Return the equivalent Python expression for a group of values

        This method is called on a group of values to transform them into an actual
        Python expression that will be placed in a `yield {rval}` statement within the
        final, compiled Jinja2 template function.

        By default, this method always returns the string values of each item in the
        group, concatenated together. We alter this method to pass-through native types
        if there is only a single value. This ensures `{{ 123 }}` becomes `yield 123`,
        while `{{ 123 }}{{ 456 }}` becomes `yield '123456'`
        """
        vals = tuple(group)
        if len(vals) == 1:
            return repr(vals[0])
        else:
            return repr("".join(map(str, vals)))


@add_template_class
class NoLiteralEvalNativeEnvironment(NativeEnvironment):
    """NativeEnvironment that treats TemplateData nodes as strings and Expr nodes as native

    >>> native = NativeEnvironment()
    >>> nolit_native = NoLiteralEvalNativeEnvironment()
    >>> native.from_string('123').render()
    123
    >>> nolit_native.from_string('123').render()
    '123'

    >>> native.from_string('{{ 123 }}').render()
    123
    >>> nolit_native.from_string('{{ 123 }}').render()
    123

    >>> native.from_string('{{ "123" }}').render()  # vanilla native even evaluates explicit strings
    123
    >>> nolit_native.from_string('{{ "123" }}').render()
    '123'
    """
    concat = staticmethod(no_literal_eval_native_concat)
    code_generator_class = NoLiteralEvalNativeCodeGenerator
    template_class = NoAsyncConcatNativeTemplate


@with_code_generator(
    NoLiteralEvalNativeCodeGenerator,
    AsyncOperandsCodeGenerator,
    NativeComprehensionCodeGenerator,
)
@add_template_class
class NoLiteralEvalComprehensionNativeEnvironment(
    NativeComprehensionEnvironment,
    NoLiteralEvalNativeEnvironment,
):
    template_class = NoAsyncConcatNativeTemplate
