"""Coordinator for yoto integration."""

from __future__ import annotations

from datetime import timedelta
from datetime import time


import logging

from yoto_api import (
    YotoManager,
    YotoPlayerConfig,
)

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class YotoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.platforms: set[str] = set()
        self.yoto_manager = YotoManager(
            username=config_entry.data.get(CONF_USERNAME),
            password=config_entry.data.get(CONF_PASSWORD),
        )
        self.scan_interval: int = (
            config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) * 60
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self):
        """Update data via library. Called by update_coordinator periodically.

        Allow to update for the first time without further checking
        """
        try:
            await self.async_check_and_refresh_token()
        except Exception as AuthError:
            raise ConfigEntryAuthFailed(AuthError) from AuthError

        await self.hass.async_add_executor_job(self.yoto_manager.update_players_status)
        if len(self.yoto_manager.library.keys()) == 0:
            await self.hass.async_add_executor_job(self.yoto_manager.update_cards)
        if self.yoto_manager.mqtt_client is None:
            self.yoto_manager.connect_to_events(self.api_callback)
        return self.data

    def api_callback(self):
        self.async_set_updated_data(self.data)

    async def release(self) -> None:
        """Disconnect from API."""
        self.yoto_manager.disconnect()

    async def async_update_all(self) -> None:
        """Update yoto data."""
        await self.async_refresh()

    async def async_check_and_refresh_token(self):
        """Refresh token if needed via library."""
        await self.hass.async_add_executor_job(
            self.yoto_manager.check_and_refresh_token
        )

    async def async_pause_player(self, player_id: str) -> None:
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.pause_player, player_id
        )

    async def async_resume_player(self, player_id: str) -> None:
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.resume_player, player_id
        )

    async def async_stop_player(self, player_id: str) -> None:
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_manager.stop_player, player_id)

    async def async_set_time(self, player_id: str, key: str, value: time) -> None:
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "day_mode_time":
            config.day_mode_time = value
        if key == "night_mode_time":
            config.night_mode_time = value
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_set_max_volume(self, player_id: str, key: str, value: time) -> None:
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "night_max_volume_limit":
            config.night_max_volume_limit = int(value)
        if key == "day_max_volume_limit":
            config.day_max_volume_limit = int(value)
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_set_brightness(self, player_id: str, key: str, value: time) -> None:
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "night_display_brightness":
            if value == "auto":
                config.night_display_brightness = value
            else:
                config.night_display_brightness = int(value)
        if key == "day_display_brightness":
            if value == "auto":
                config.day_display_brightness = value
            else:
                config.day_display_brightness = int(value)
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_play_card(
        self,
        player_id: str,
        cardid: str,
        secondsin: int = 0,
        cutoff: int = 0,
        chapter: int = 1,
        trackkey: int = 1,
    ) -> None:
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.play_card,
            player_id,
            cardid,
            secondsin,
            cutoff,
            chapter,
            trackkey,
        )

    async def async_set_volume(self, player_id: str, volume: float) -> None:
        volume = volume * 100
        volume = int(round(volume, 0))
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_volume, player_id, volume
        )
