from __future__ import annotations

import typing as t

from jinja2.lexer import describe_token
from jinja2.nodes import Keyword
from jinja2.parser import Parser

from jinja_comprehensions import nodes

N = t.TypeVar('N', bound=nodes.Node)


class ComprehensionParser(Parser):
    def parse_tuple(
        self,
        simplified: bool = False,
        with_condexpr: bool = True,
        extra_end_rules: t.Optional[t.Tuple[str, ...]] = None,
        explicit_parentheses: bool = False,
        with_comprehension: bool = True,
    ) -> nodes.Tuple | nodes.Expr | nodes.Generator:
        lineno = self.stream.current.lineno
        if simplified:
            parse = self.parse_primary
        elif with_condexpr:
            parse = self.parse_expression
        else:

            def parse() -> nodes.Expr:
                return self.parse_expression(with_condexpr=False)

        args: t.List[nodes.Expr] = []
        is_tuple = False

        while True:
            if args:
                self.stream.expect("comma")

            if self.is_tuple_end(extra_end_rules):
                break

            if with_condexpr and not simplified and self.stream.current.type == "mul":
                item = self._parse_spread_scalars()
            else:
                item = parse()
            args.append(item)

            if self.stream.current.type == "comma":
                is_tuple = True
            elif with_comprehension and len(args) == 1 and self.stream.skip_if('name:for'):
                return self._parse_comprehension(nodes.Generator, args[0], 'rparen', eat_end=False)
            else:
                break

            lineno = self.stream.current.lineno

        if not is_tuple:
            if args:
                return args[0]

            # if we don't have explicit parentheses, an empty tuple is
            # not a valid expression.  This would mean nothing (literally
            # nothing) in the spot of an expression would be an empty
            # tuple.
            if not explicit_parentheses:
                self.fail(
                    "Expected an expression,"
                    f" got {describe_token(self.stream.current)!r}"
                )

        return nodes.Tuple(args, "load", lineno=lineno)

    def parse_list(self) -> nodes.List | nodes.ListComprehension:
        token = self.stream.expect('lbracket')
        items: t.List[nodes.Expr] = []
        while self.stream.current.type != 'rbracket':
            if items:
                if len(items) == 1 and self.stream.skip_if('name:for'):
                    return self._parse_comprehension(nodes.ListComprehension, items[0], 'rbracket')
                else:
                    self.stream.expect('comma')

            if self.stream.current.type == 'rbracket':
                break

            if self.stream.current.type == 'mul':
                item = self._parse_spread_scalars()
            else:
                item = self.parse_expression()

            items.append(item)

        self.stream.expect('rbracket')
        return nodes.List(items, lineno=token.lineno)

    def parse_dict(
        self
    ) -> nodes.Dict | nodes.Set | nodes.DictComprehension | nodes.SetComprehension:
        token = self.stream.expect("lbrace")
        items: t.List[nodes.Pair | nodes.SpreadPairs | nodes.Expr | nodes.SpreadScalars] = []
        is_set: bool | None = None
        while self.stream.current.type != "rbrace":
            if items:
                if len(items) == 1 and self.stream.skip_if('name:for'):
                    comp_type = nodes.SetComprehension if is_set else nodes.DictComprehension
                    return self._parse_comprehension(comp_type, items[0], 'rbrace')
                self.stream.expect("comma")

            if self.stream.current.type == "rbrace":
                break

            if (is_set is None or is_set is False) and self.stream.skip_if("pow"):
                items.append(nodes.SpreadPairs(self.parse_expression(), lineno=token.lineno))
                continue
            elif (is_set is None or is_set is True) and self.stream.current.type == "mul":
                items.append(self._parse_spread_scalars())
                continue

            key = self.parse_expression()
            if is_set is None:
                is_set = self.stream.current.type != "colon"

            if is_set:
                item = key
            else:
                self.stream.expect("colon")
                value = self.parse_expression()
                item = nodes.Pair(key, value, lineno=key.lineno)

            items.append(item)

        self.stream.expect("rbrace")
        node_cls = nodes.Set if is_set else nodes.Dict
        return node_cls(items, lineno=token.lineno)

    def _parse_spread_scalars(self) -> nodes.SpreadScalars:
        """Parse a spread scalar expression, e.g. `*base`.

        The current token is expected to be an asterisk (mul token).
        """
        token = self.stream.current
        self.stream.expect('mul')
        return nodes.SpreadScalars(self.parse_expression(), lineno=token.lineno)

    def _parse_comprehension(
        self, node_cls: t.Type[N], iterand: nodes.Node, end_type: str, *, eat_end: bool = True
    ) -> N:
        for_components = []
        while self.stream.current.type != end_type:
            target = self.parse_assign_target(extra_end_rules=('name:in',))
            self.stream.expect('name:in')
            iter = self.parse_tuple(
                with_condexpr=False, extra_end_rules=('name:if',), with_comprehension=False
            )
            cond = None
            if self.stream.skip_if('name:if'):
                cond = self.parse_expression()
            for_components.append(nodes.ComprehensionComponent(target, iter, cond))

            if not self.stream.skip_if('name:for'):
                break

        if eat_end:
            self.stream.expect(end_type)

        return node_cls(for_components, iterand)

    def parse_call_args(self) -> t.Tuple:
        token = self.stream.expect("lparen")
        args = []
        kwargs = []
        dyn_args = None
        dyn_kwargs = None
        require_comma = False

        def ensure(expr: bool) -> None:
            if not expr:
                self.fail("invalid syntax for function call expression", token.lineno)

        while self.stream.current.type != "rparen":
            if require_comma:
                self.stream.expect("comma")

                # support for trailing comma
                if self.stream.current.type == "rparen":
                    break

            if self.stream.current.type == "mul":
                ensure(dyn_args is None and dyn_kwargs is None)
                next(self.stream)
                dyn_args = self.parse_expression()
            elif self.stream.current.type == "pow":
                ensure(dyn_kwargs is None)
                next(self.stream)
                dyn_kwargs = self.parse_expression()
            else:
                if (
                    self.stream.current.type == "name"
                    and self.stream.look().type == "assign"
                ):
                    # Parsing a kwarg
                    ensure(dyn_kwargs is None)
                    key = self.stream.current.value
                    self.stream.skip(2)
                    value = self.parse_expression()
                    kwargs.append(Keyword(key, value, lineno=value.lineno))
                else:
                    # Parsing an arg
                    ensure(dyn_args is None and dyn_kwargs is None and not kwargs)
                    args.append(self.parse_expression())

                    # If we're the first arg, we might have a generator
                    if len(args) == 1 and self.stream.skip_if('name:for'):
                        generator = self._parse_comprehension(
                            nodes.Generator, args[0], 'rparen', eat_end=False
                        )
                        args[0] = generator

            require_comma = True

        self.stream.expect("rparen")
        return args, kwargs, dyn_args, dyn_kwargs
