from __future__ import annotations

from jinja2 import nodes
from jinja2.environment import Environment

from jinja_comprehensions import compiler, parser

__all__ = ['ComprehensionEnvironment']


class ComprehensionEnvironment(Environment):
    code_generator_class = compiler.ComprehensionCodeGenerator

    def _parse(
        self, source: str, name: str | None, filename: str | None
    ) -> nodes.Template:
        return parser.ComprehensionParser(self, source, name, filename).parse()
