"""Wrapper for service module to add types."""

from typing import TYPE_CHECKING

import services
from sims.sim_info_manager import SimInfoManager

from .clientmanager import ClientManager

if TYPE_CHECKING:
    import server


def client_manager() -> ClientManager:
    """Typed version of services.client_manager."""
    manager: server.clientmanager.ClientManager = services.client_manager()

    return ClientManager(manager)


def sim_info_manager() -> SimInfoManager:
    """Typed version of services.sim_info_manager."""
    return services.sim_info_manager()
