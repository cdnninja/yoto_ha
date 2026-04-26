"""Yoto integration services."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator

SERVICE_UPDATE = "update"

SUPPORTED_SERVICES = (SERVICE_UPDATE,)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Yoto."""

    async def async_handle_update(call: ServiceCall) -> None:
        _LOGGER.debug(f"Call:{call.data}")
        coordinator = _get_coordinator_from_device(hass, call)
        await coordinator.async_update_all()

    services = {SERVICE_UPDATE: async_handle_update}

    for service in SUPPORTED_SERVICES:
        hass.services.async_register(DOMAIN, service, services[service])


def _get_coordinator_from_device(
    hass: HomeAssistant, call: ServiceCall
) -> YotoDataUpdateCoordinator:
    """Get the coordinator targeted by the service call."""
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state == ConfigEntryState.LOADED
    ]
    if not entries:
        raise ServiceValidationError("No loaded Yoto config entry found")

    if len(entries) == 1:
        return entries[0].runtime_data

    device_entry = device_registry.async_get(hass).async_get(call.data[ATTR_DEVICE_ID])
    if device_entry is None:
        raise ServiceValidationError("Device not found")

    for entry in entries:
        if entry.entry_id in device_entry.config_entries:
            return entry.runtime_data

    raise ServiceValidationError("No Yoto config entry for the requested device")
