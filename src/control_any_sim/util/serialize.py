"""Serialization and deserialization functions to store objects as JSON."""

from __future__ import annotations

import json
from typing import Any, Callable, Protocol, TypeVar

C = TypeVar("C")


def dict_to_obj(cls: type[C]) -> Callable[[dict[str, Any]], C]:
    """Convert a dict into an object."""

    def hook(our_dict: dict[str, Any]) -> C:
        # Use dictionary unpacking to initialize the object
        return cls(**our_dict)

    return hook


def object_to_dict(obj: object) -> dict[str, Any]:
    """
    Convert object to dict.

    Takes in a custom object and returns a dictionary representation
    of the object. This dict representation includes meta data such as the
    object's module and class names.
    """
    #  Populate the dictionary with object meta data
    obj_dict = {"__class__": obj.__class__.__name__, "__module__": obj.__module__}

    #  Populate the dictionary with object properties
    obj_dict.update(obj.__dict__)

    return obj_dict


class Serializable(Protocol):
    """Class that can be serialized to JSON."""

    def serialize(self: object) -> str:
        """Serialize an object into a JSON string."""
        return json.dumps(self, default=object_to_dict, indent=4, sort_keys=True)

    @classmethod
    def deserialize(cls: type[C], data: str) -> C:
        """Deserialize an object from a JSON string."""
        return json.loads(data, object_hook=dict_to_obj(cls))
