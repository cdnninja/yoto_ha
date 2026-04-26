"""Yoto integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType
from yoto_api import AuthenticationError

from .const import CONF_TOKEN, DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .media_source import YotoMediaSource
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.TIME,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Yoto component."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: YotoConfigEntry) -> bool:
    """Set up Yoto from a config entry."""
    coordinator = YotoDataUpdateCoordinator(hass, config_entry)
    try:
        await coordinator.async_config_entry_first_refresh()
        await asyncio.sleep(3)
    except AuthenticationError as ex:
        _LOGGER.error(f"Authentication error: {ex}")
        raise ConfigEntryAuthFailed from ex

    config_entry.runtime_data = coordinator

    async def _handle_shutdown(event):
        new_data = dict(config_entry.data)
        new_data[CONF_TOKEN] = coordinator.yoto_manager.token.refresh_token
        _LOGGER.debug("Storing token on HA shutdown.")
        hass.config_entries.async_update_entry(config_entry, data=new_data)

    hass.bus.async_listen_once("homeassistant_stop", _handle_shutdown)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    hass.data.setdefault("media_source", {})
    hass.data["media_source"][DOMAIN] = YotoMediaSource(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: YotoConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = entry.runtime_data
    if coordinator.yoto_manager.token.refresh_token != entry.data.get(CONF_TOKEN):
        new_data = dict(entry.data)
        new_data[CONF_TOKEN] = coordinator.yoto_manager.token.refresh_token
        _LOGGER.debug("Storing token on unload")
        hass.config_entries.async_update_entry(entry, data=new_data)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await coordinator.release()
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if entry.version < 2:
        _LOGGER.debug("Migrating entry to version 2")
        data = dict(entry.data)
        data.pop(CONF_USERNAME, None)
        data.pop(CONF_PASSWORD, None)
        hass.config_entries.async_update_entry(entry=entry, data=data, version=2)
        _LOGGER.debug("Migration to version 2 successful")
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: YotoConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
