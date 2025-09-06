import logging
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from yoto_api import AuthenticationError


from .media_source import YotoMediaSource
from .const import DOMAIN, CONF_TOKEN
from .coordinator import YotoDataUpdateCoordinator
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


async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry):
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Yoto from a config entry."""
    coordinator = YotoDataUpdateCoordinator(hass, config_entry)
    try:
        await coordinator.async_config_entry_first_refresh()
        await asyncio.sleep(2)
    except AuthenticationError as ex:
        _LOGGER.error(f"Authentication error: {ex}")
        raise ConfigEntryAuthFailed from ex

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.unique_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    async_setup_services(hass)

    # Register the media source
    hass.data.setdefault("media_source", {})
    hass.data["media_source"][DOMAIN] = YotoMediaSource(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        release_tasks = set()
        coordinator = hass.data[DOMAIN][entry.unique_id]
        release_tasks.add(coordinator.release())
        new_data = dict(entry.data)
        new_data[CONF_TOKEN] = coordinator.yoto_manager.token
        hass.config_entries.async_update_entry(entry, data=new_data)
        hass.data[DOMAIN].pop(entry.unique_id)
        await asyncio.gather(*release_tasks)
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
