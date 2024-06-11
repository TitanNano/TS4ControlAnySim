"""Serialization and deserialization functions to store objects as JSON."""

from __future__ import annotations

import json
from typing import Any, Callable, TypeVar

C = TypeVar("C")


def dict_to_obj(cls: type[C]) -> Callable[[dict[str, Any]], C]:
    """Convert a dict into an object."""

    def hook(our_dict: dict[str, Any]) -> C:
        if "__class__" in our_dict:
            del our_dict["__class__"]

        if "__module__" in our_dict:
            del our_dict["__module__"]

        # Use dictionary unpacking to initialize the object
        return cls(**our_dict)

    return hook


def object_to_dict(obj: object) -> dict[str, Any]:
    """
    Convert object to dict.

    Takes in a custom object and returns a dictionary representation
    of the object.
    """
    return obj.__dict__


class Serializable:
    """Class that can be serialized to JSON."""

    def serialize(self: object) -> str:
        """Serialize an object into a JSON string."""
        return json.dumps(self, default=object_to_dict, indent=4, sort_keys=True)

    @classmethod
    def deserialize(cls: type[C], data: str) -> C:
        """Deserialize an object from a JSON string."""
        return json.loads(data, object_hook=dict_to_obj(cls))
