"""Mod injection utility."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import distributor

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

T = TypeVar("T")
NewFun: TypeAlias = Callable[..., T]


# method calling injection
def inject(
    target_function: Callable[..., T],
    new_function: Callable[..., T],
) -> Callable[..., T]:
    """
    Inject a wrapper method into an existing class.

    Replaces the original method.
    """

    @wraps(target_function)
    def _inject(*args: list[Any], **kwargs: list[Any]) -> T:
        return new_function(target_function, *args, **kwargs)

    return _inject


def inject_method_to(
    target_object: object,
    target_function_name: str,
) -> Callable[[NewFun], NewFun]:
    """
    Inject a wrapper method into an existing class.

    Replaces the original method.
    """

    def _inject_to(new_function: NewFun) -> NewFun:
        target_function = getattr(target_object, target_function_name)

        setattr(
            target_object,
            target_function_name,
            inject(target_function, new_function),
        )

        return new_function

    return _inject_to


# class field injection
def inject_field_to(
    target_object: object,
    target_function: str,
    operator: str,
) -> Callable[[NewFun], NewFun]:
    """
    Inject a wrapper field into an existing class.

    Replaces the existing field getter with the new one.
    """

    def _inject_to(new_getter: NewFun) -> NewFun:
        target_field = getattr(target_object, target_function)
        target_getter = target_field.getter

        injected_getter = inject(target_getter, new_getter)
        new_field = distributor.fields.Field(getter=injected_getter, op=operator)

        setattr(target_object, target_function, new_field)

        return new_getter

    return _inject_to


# class property injection
def inject_property_to(
    target_object: object,
    target_function: str,
) -> Callable[[NewFun], NewFun]:
    """
    Inject a wrapper property into an existing class.

    Replaces the existing property getter with the new one.
    """

    def _inject_to(new_getter: NewFun) -> NewFun:
        target_property = getattr(target_object, target_function)
        target_getter = target_property.__get__

        injected_getter = inject(target_getter, new_getter)
        new_property = property(injected_getter)

        setattr(target_object, target_function, new_property)

        return new_getter

    return _inject_to
