"""Wrapper for server.clientmanager."""

from __future__ import annotations

from typing import TYPE_CHECKING

import services

if TYPE_CHECKING:
    from server import clientmanager
    from server.client import Client
    from typing_extensions import Self


class ClientManager:
    """Wrapper for server.clientmanager."""

    inner: clientmanager.ClientManager

    def __init__(self: Self, inner: clientmanager.ClientManager) -> None:
        """Create a new wrapper instance."""
        self.inner = inner

    def get_client_by_household_id(self: Self, household_id: int) -> Client | None:
        """Get a game client by household id."""
        return self.inner.get_client_by_household_id(household_id)

    def get_active_client(self: Self) -> Client | None:
        """Get the client of the active household."""
        return self.get_client_by_household_id(services.active_household_id())
