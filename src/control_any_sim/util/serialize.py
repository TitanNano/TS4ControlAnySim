"""Serialization and deserialization functions to store objects as JSON."""

from __future__ import annotations

import json
from typing import Any, Callable, TypeVar

from typing_extensions import Self

C = TypeVar("C")


def dict_to_obj(cls: type[C]) -> Callable[[dict[str, Any]], C]:
    """
    Convert a dict into an object.

    Returns
    -------
        A function that converts an object into a dictionary.

    """

    def hook(our_dict: dict[str, Any]) -> C:
        our_dict.pop("__class__", None)

        our_dict.pop("__module__", None)

        # Use dictionary unpacking to initialize the object
        return cls(**our_dict)

    return hook


def object_to_dict(obj: object) -> dict[str, Any]:
    """
    Convert object to dict.

    Takes in a custom object

    Returns
    -------
        A dictionary representation of the object.

    """
    return obj.__dict__


class Serializable:
    """Class that can be serialized to JSON."""

    def serialize(self: object) -> str:
        """
        Serialize an object into a JSON string.

        Returns
        -------
            A JSON string of the serialized data.

        """
        return json.dumps(self, default=object_to_dict, indent=4, sort_keys=True)

    @classmethod
    def deserialize(cls, data: str) -> Self:
        """
        Deserialize an object from a JSON string.

        Returns
        -------
            A new instance of Self.

        """
        return json.loads(data, object_hook=dict_to_obj(cls))
