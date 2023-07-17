from __future__ import annotations

from typing import Callable

from jinja2.compiler import CodeGenerator, Frame, operators
from jinja2.nodes import Template, Operand

from jinja_comprehensions import nodes

__all__ = [
    'AsyncOperandsCodeGenerator',
    'ComprehensionCodeGenerator',
]


class AsyncOperandsCodeGenerator(CodeGenerator):
    def visit_Template(self, node: Template, frame: Frame | None = None) -> None:
        if self.environment.is_async:
            self.writeline('from jinja_comprehensions.runtime import syncify_awaitable')
        super().visit_Template(node, frame)

    def visit_Operand(self, node: Operand, frame: Frame) -> None:
        if self.environment.is_async and node.op == 'in':
            self.write(f' {operators[node.op]} ')
            self.write('(await syncify_awaitable(')
            self.visit(node.expr, frame)
            self.write('))')
        else:
            super().visit_Operand(node, frame)


class ComprehensionCodeGenerator(CodeGenerator):
    def visit_Set(self, node: nodes.Set, frame: Frame) -> None:
        self.write("{")
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            self.visit(item, frame)
        self.write(",}")

    def visit_SpreadScalars(self, node: nodes.SpreadScalars, frame: Frame) -> None:
        self.write("*")
        self.visit(node.node, frame)

    def visit_Dict(self, node: nodes.Dict, frame: Frame) -> None:
        self.write("{")
        for idx, item in enumerate(node.items):
            if idx:
                self.write(", ")
            if isinstance(item, nodes.SpreadPairs):
                self.visit(item, frame)
            else:
                self.visit(item.key, frame)
                self.write(": ")
                self.visit(item.value, frame)
        self.write("}")

    def visit_SpreadPairs(self, node: nodes.SpreadPairs, frame: Frame) -> None:
        self.write("**")
        self.visit(node.node, frame)

    def visit_Generator(self, node: nodes.Generator, frame: Frame) -> None:
        self._scalar_comprehension(node, frame, "(", ")")

    def visit_ListComprehension(self, node: nodes.ListComprehension, frame: Frame) -> None:
        self._scalar_comprehension(node, frame, "[", "]")

    def visit_SetComprehension(self, node: nodes.SetComprehension, frame: Frame) -> None:
        self._scalar_comprehension(node, frame, "{", "}")

    def visit_DictComprehension(self, node: nodes.DictComprehension, frame: Frame) -> None:
        self.write("{")

        def write_expr(expr_frame: Frame):
            self.visit(node.pair.key, expr_frame)
            self.write(": ")
            self.visit(node.pair.value, expr_frame)

        self._comprehension_common(node, frame, write_expr)

        self.write("}")

    def _scalar_comprehension(
        self,
        node: nodes.Generator | nodes.ListComprehension | nodes.SetComprehension,
        frame: Frame,
        prefix: str,
        suffix: str,
    ) -> None:
        self.write(prefix)

        def write_expr(expr_frame: Frame):
            self.visit(node.expr, expr_frame)

        self._comprehension_common(node, frame, write_expr)

        self.write(suffix)

    def _comprehension_common(
        self,
        node: nodes.Generator | nodes.ListComprehension | nodes.DictComprehension,
        outer_frame: Frame,
        write_expr: Callable[[Frame], None],
    ) -> None:
        frames = []
        iter_frame = outer_frame
        for i in range(len(node.for_components)):
            loop_frame = iter_frame.inner()
            frames.insert(0, (iter_frame, loop_frame))
            iter_frame = loop_frame

        expr_frame = frames[0][1]
        write_expr(expr_frame)

        for component, (iter_frame, loop_frame) in zip(node.for_components, frames):
            self.write(self.choose_async(" async for ", " for "))
            self.visit(component.target, loop_frame)
            self.write(" in ")
            self.write(self.choose_async("auto_aiter(", ""))
            self.visit(component.iter, iter_frame)
            self.write(self.choose_async(")", ""))

            if component.cond:
                self.write(" if ")
                self.visit(component.cond, loop_frame)
