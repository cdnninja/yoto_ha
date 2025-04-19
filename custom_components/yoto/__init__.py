import logging
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed
from yoto_api import AuthenticationError


from .media_source import YotoMediaSource
from .const import DOMAIN
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

        raise ConfigEntryAuthFailed
    except Exception as ex:
        raise ConfigEntryNotReady(f"Config Not Ready: {ex}")

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
        hass.data[DOMAIN].pop(entry.unique_id)
        await asyncio.gather(*release_tasks)
    return unload_ok
