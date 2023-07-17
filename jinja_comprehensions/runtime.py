from __future__ import annotations

from typing import Any, AsyncIterable, Awaitable

import asyncstdlib
from jinja2 import Undefined


async def syncify_awaitable(v: Any | Awaitable[Any] | AsyncIterable[Any]) -> Any:
    if isinstance(v, Undefined):
        # Deliberately avoid calling isinstance() on an Undefined,
        # as attr access of __class__ may raise an UndefinedError.
        pass
    elif isinstance(v, AsyncIterable):
        v = await asyncstdlib.list(v)
    elif isinstance(v, Awaitable):
        v = await v

    return v
