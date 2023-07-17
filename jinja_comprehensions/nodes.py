from __future__ import annotations

from typing import Any

from jinja2.nodes import (
    EvalContext,
    Expr,
    get_eval_context,
    Literal,
    NodeType, Helper, Pair, Node,
)


class CustomNodeType(NodeType):

    ###
    # NOTE:
    #   Jinja2 disables the creation of new nodes by deleting NodeType.__new__,
    #   replacing it with a method that simply raises an exception. This metaclass
    #   reproduces the original __new__ method.
    #

    def __new__(mcs, name, bases, d):  # type: ignore
        for attr in "fields", "attributes":
            storage = []
            storage.extend(getattr(bases[0] if bases else object, attr, ()))
            storage.extend(d.get(attr, ()))
            assert len(bases) <= 1, "multiple inheritance not allowed"
            assert len(storage) == len(set(storage)), "layout conflict"
            d[attr] = tuple(storage)
        d.setdefault("abstract", False)
        return type.__new__(mcs, name, bases, d)


class Tuple(Literal, metaclass=CustomNodeType):
    """For loop unpacking and some other things like multiple arguments
    for subscripts.  Like for :class:`Name` `ctx` specifies if the tuple
    is used for loading the names or storing.
    """

    fields = ("items", "ctx")
    items: list[Expr | SpreadScalars]
    ctx: str

    def as_const(self, eval_ctx: EvalContext | None = None) -> tuple[Any, ...]:
        eval_ctx = get_eval_context(self, eval_ctx)
        items = []
        for item in self.items:
            if isinstance(item, SpreadScalars):
                items.extend(item.as_const(eval_ctx))
            else:
                items.append(item.as_const(eval_ctx))
        return tuple(items)

    def can_assign(self) -> bool:
        for item in self.items:
            if not item.can_assign():
                return False
        return True


class List(Literal, metaclass=CustomNodeType):
    """Any list literal such as ``[1, 2, 3]``."""

    fields = ("items",)
    items: list[Expr | SpreadScalars]

    def as_const(self, eval_ctx: EvalContext | None = None) -> list[Any]:
        eval_ctx = get_eval_context(self, eval_ctx)
        items = []
        for item in self.items:
            if isinstance(item, SpreadScalars):
                items.extend(item.as_const(eval_ctx))
            else:
                items.append(item.as_const(eval_ctx))
        return items


class Set(Literal, metaclass=CustomNodeType):
    """Any set literal such as ``{1, 2, 3}``"""

    fields = ("items",)
    items: list[Expr | SpreadScalars]

    def as_const(self, eval_ctx: EvalContext | None = None) -> set[Any]:
        eval_ctx = get_eval_context(self, eval_ctx)
        items = set()
        for item in self.items:
            if isinstance(item, SpreadScalars):
                items.update(item.as_const(eval_ctx))
            else:
                items.add(item.as_const(eval_ctx))
        return items


class SpreadScalars(Helper, metaclass=CustomNodeType):
    """A scalar-valued collection spread such as ``*base``."""

    fields = ("node",)
    node: Expr

    def as_const(self, eval_ctx: EvalContext | None = None) -> list[Any]:
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.node.as_const(eval_ctx)


class Dict(Literal, metaclass=CustomNodeType):
    """Any dict literal such as ``{1: 2, 3: 4, **base, **other, 5: 6}``.

    The items must be a list of :class:`Pair` or :class:`DictSpread` nodes.
    """

    fields = ("items",)
    items: list[Pair | SpreadPairs]

    def as_const(
        self, eval_ctx: EvalContext | None = None
    ) -> dict[Any, Any]:
        eval_ctx = get_eval_context(self, eval_ctx)
        items = []
        for item in self.items:
            if isinstance(item, SpreadPairs):
                items.extend(item.as_const(eval_ctx).items())
            else:
                items.append(item.as_const(eval_ctx))
        return dict(items)


class SpreadPairs(Helper, metaclass=CustomNodeType):
    """A dict spread such as ``**base``."""

    fields = ("node",)
    node: Expr

    def as_const(self, eval_ctx: EvalContext | None = None) -> dict[Any, Any]:
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.node.as_const(eval_ctx)


class ComprehensionComponent(Expr, metaclass=CustomNodeType):
    fields = ('target', 'iter', 'cond')
    target: Node
    iter: Node
    cond: Node | None


class _BaseComprehension(Expr, metaclass=CustomNodeType):
    fields = ('for_components',)
    for_components: list[ComprehensionComponent]

    ###
    # NB(zk) --
    #
    # When first implementing this, for_components was a list of tuples (target, iter, cond);
    # for some reason, this led to strange reference errors during template compilation. For
    # instance, the template `{{ [i for i in range(10)] }}` led to:
    #   AssertionError: Tried to resolve a name to a reference that was unknown to the frame ('range')
    #
    # This error disappeared when for_components changed from a list of tuples to a list of Nodes.
    #


class Generator(_BaseComprehension, metaclass=CustomNodeType):
    fields = ('expr',)
    expr: Expr


class ListComprehension(_BaseComprehension, metaclass=CustomNodeType):
    fields = ('expr',)
    expr: Expr


class SetComprehension(_BaseComprehension, metaclass=CustomNodeType):
    fields = ('expr',)
    expr: Expr


class DictComprehension(_BaseComprehension, metaclass=CustomNodeType):
    fields = ('pair',)
    pair: Pair
