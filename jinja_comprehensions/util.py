from __future__ import annotations

from typing import Callable, Type, TypeVar, cast

import jinja2
import jinja2.compiler

__all__ = [
    'create_template_class',
    'add_template_class',
    'with_code_generator',
]


def create_template_class(
    name: str, environment_class: Type[jinja2.Environment]
) -> Type[jinja2.Template]:
    """Create a template class pointed at the specified Environment class"""
    base = environment_class.template_class
    template_class = type(name, (base,), {'environment_class': environment_class})
    return cast(Type[jinja2.Template], template_class)


EnvT = TypeVar('EnvT', bound=Type[jinja2.Environment])


def add_template_class(environment_class: EnvT) -> EnvT:
    """Class decorator to construct and assign a template class to an Environment"""
    base_name = _get_env_base_name(environment_class)
    template_class_name = f'{base_name}Template'
    environment_class.template_class = create_template_class(template_class_name, environment_class)
    return environment_class


def with_code_generator(
    base: Type[jinja2.compiler.CodeGenerator],
    *other_bases: Type[jinja2.compiler.CodeGenerator],
) -> Callable[[EnvT], EnvT]:
    """Class decorator to construct and assign a CodeGenerator class to an Environment"""
    def _with_code_generator_decorator(environment_class: EnvT) -> EnvT:
        if other_bases:
            base_name = _get_env_base_name(environment_class)
            code_generator_class_name = f'{base_name}CodeGenerator'
            code_generator_class = type(code_generator_class_name, (base, *other_bases), {})
        else:
            code_generator_class = base

        environment_class.code_generator_class = code_generator_class
        return environment_class

    return _with_code_generator_decorator


def _get_env_base_name(environment_class: Type[jinja2.Environment]) -> str:
    return environment_class.__name__.removesuffix('Environment')
