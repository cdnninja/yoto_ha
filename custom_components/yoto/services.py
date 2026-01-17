import logging
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator

SERVICE_UPDATE = "update"

SUPPORTED_SERVICES = (SERVICE_UPDATE,)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> bool:
    """Set up services for Yoto"""

    async def async_handle_update(call: ServiceCall) -> None:
        _LOGGER.debug(f"Call:{call.data}")
        coordinator = _get_coordinator_from_device(hass, call)
        await coordinator.async_update_all()

    services: dict[str, object] = {SERVICE_UPDATE: async_handle_update}

    for service in SUPPORTED_SERVICES:
        hass.services.async_register(DOMAIN, service, services[service])
    return True


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    for service in SUPPORTED_SERVICES:
        hass.services.async_remove(DOMAIN, service)


def _get_player_id_from_device(hass: HomeAssistant, call: ServiceCall) -> str:
    """Get player ID from device registry."""
    coordinators = list(hass.data[DOMAIN].keys())
    if len(coordinators) == 1:
        coordinator = hass.data[DOMAIN][coordinators[0]]
        players = coordinator.yoto_manager.players
        if len(players) == 1:
            return list(players.keys())[0]

    device_entry = device_registry.async_get(hass).async_get(call.data[ATTR_DEVICE_ID])
    for entry in device_entry.identifiers:
        if entry[0] == DOMAIN:
            player_id = entry[1]
    return player_id


def _get_coordinator_from_device(
    hass: HomeAssistant, call: ServiceCall
) -> YotoDataUpdateCoordinator:
    """Get coordinator from device registry."""
    coordinators = list(hass.data[DOMAIN].keys())
    if len(coordinators) == 1:
        return hass.data[DOMAIN][coordinators[0]]
    else:
        device_entry = device_registry.async_get(hass).async_get(
            call.data[ATTR_DEVICE_ID]
        )
        config_entry_ids = device_entry.config_entries
        config_entry_id = next(
            (
                config_entry_id
                for config_entry_id in config_entry_ids
                if cast(
                    ConfigEntry,
                    hass.config_entries.async_get_entry(config_entry_id),
                ).domain
                == DOMAIN
            ),
            None,
        )
        config_entry_unique_id = hass.config_entries.async_get_entry(
            config_entry_id
        ).unique_id
        return hass.data[DOMAIN][config_entry_unique_id]
