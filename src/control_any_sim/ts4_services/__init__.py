"""Wrapper for service module to add types."""
from __future__ import annotations

from typing import TYPE_CHECKING

import services

from .clientmanager import ClientManager

if TYPE_CHECKING:
    import server
    from sims.sim_info_manager import SimInfoManager
    from sims.sim_spawner_service import SimSpawnerService


def client_manager() -> ClientManager:
    """Typed version of services.client_manager."""
    manager: server.clientmanager.ClientManager = services.client_manager()

    return ClientManager(manager)


def sim_info_manager() -> SimInfoManager:
    """Typed version of services.sim_info_manager."""
    return services.sim_info_manager()


def sim_spawner_service(zone_id: int | None = None) -> SimSpawnerService:
    """Typed version of services.sim_spawner_manager."""
    return services.sim_spawner_service(zone_id)
