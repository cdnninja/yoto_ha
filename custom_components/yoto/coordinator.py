"""Coordinator for yoto integration."""

from __future__ import annotations

import logging
from datetime import time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from yoto_api import AuthenticationError, YotoManager, YotoPlayerConfig

from .const import CONF_TOKEN, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class YotoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.platforms: set[str] = set()
        self.config_entry = config_entry
        self.yoto_manager = YotoManager(client_id="KFLTf5PCpTh0yOuDuyQ5C3LEU9PSbult")
        if config_entry.data.get(CONF_TOKEN):
            _LOGGER.debug("Using stored token")
            self.yoto_manager.set_refresh_token(config_entry.data.get(CONF_TOKEN))
        else:
            raise ConfigEntryAuthFailed("No token configured")
        self.scan_interval: int = (
            config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) * 60
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self) -> dict | None:
        """Update data via library. Called by update_coordinator periodically.

        Allow to update for the first time without further checking
        """

        try:
            await self.async_check_and_refresh_token()
            if self.yoto_manager.token.refresh_token != self.config_entry.data.get(
                CONF_TOKEN
            ):
                new_data = dict(self.config_entry.data)
                new_data[CONF_TOKEN] = self.yoto_manager.token.refresh_token
                _LOGGER.debug("Storing updated token")
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
        except AuthenticationError as ex:
            _LOGGER.error(f"Authentication error: {ex}")
            raise ConfigEntryAuthFailed

        await self.hass.async_add_executor_job(self.yoto_manager.update_players_status)
        if len(self.yoto_manager.library.keys()) == 0:
            await self.hass.async_add_executor_job(self.yoto_manager.update_library)
        if self.yoto_manager.mqtt_client is None:
            await self.hass.async_add_executor_job(
                self.yoto_manager.connect_to_events, self.api_callback
            )
        return self.data

    def api_callback(self) -> None:
        """Handle API callback for media player updates."""
        for player in self.yoto_manager.players.values():
            if player.card_id and player.chapter_key:
                if (
                    player.card_id not in self.yoto_manager.library
                    or not self.yoto_manager.library[player.card_id].chapters
                ):
                    self.hass.add_job(self.async_update_card_detail, player.card_id)
                else:
                    if (
                        player.chapter_key
                        not in self.yoto_manager.library[player.card_id].chapters
                    ):
                        self.hass.add_job(self.async_update_card_detail, player.card_id)
        self.async_update_listeners()

    async def release(self) -> None:
        """Disconnect from API."""
        self.yoto_manager.disconnect()

    async def async_update_all(self) -> None:
        """Update yoto data."""
        await self.async_refresh()

    async def async_check_and_refresh_token(self) -> None:
        """Refresh token if needed via library."""
        await self.hass.async_add_executor_job(
            self.yoto_manager.check_and_refresh_token
        )

    async def async_pause_player(self, player_id: str) -> None:
        """Pause playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.pause_player, player_id
        )

    async def async_resume_player(self, player_id: str) -> None:
        """Resume playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.resume_player, player_id
        )

    async def async_stop_player(self, player_id: str) -> None:
        """Stop playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_manager.stop_player, player_id)

    async def async_set_time(self, player_id: str, key: str, value: time) -> None:
        """Set time for day/night mode."""
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "day_mode_time":
            config.day_mode_time = value
        if key == "night_mode_time":
            config.night_mode_time = value
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_set_max_volume(self, player_id: str, key: str, value: int) -> None:
        """Set maximum volume for day/night mode."""
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "config.night_max_volume_limit":
            config.night_max_volume_limit = int(value)
        if key == "config.day_max_volume_limit":
            config.day_max_volume_limit = int(value)
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_set_brightness(self, player_id: str, key: str, value: str) -> None:
        """Set display brightness for day/night mode."""
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if (
            key == "config.night_display_brightness"
            or key == "night_display_brightness"
        ):
            if value == "auto":
                config.night_display_brightness = value
            else:
                config.night_display_brightness = int(value)
        if key == "config.day_display_brightness" or key == "day_display_brightness":
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
        secondsin: int = None,
        cutoff: int = None,
        chapter: int = None,
        trackkey: int = None,
    ) -> None:
        """Play a card on the player."""
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
        """Set player volume level."""
        volume = volume * 100
        volume = int(round(volume, 0))
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_volume, player_id, volume
        )

    async def async_set_sleep_timer(self, player_id: str, time: int) -> None:
        """Set sleep timer on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_sleep, player_id, int(time)
        )

    async def async_set_light(self, player_id: str, key: str, color: str) -> None:
        """Set light color for day/night ambient mode."""
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        if key == "config.day_ambient_colour":
            config.day_ambient_colour = color
        elif key == "config.night_ambient_colour":
            config.night_ambient_colour = color
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_enable_disable_alarm(
        self, player_id: str, alarm: int, enable: bool
    ) -> None:
        """Enable or disable an alarm."""
        await self.async_check_and_refresh_token()
        config = YotoPlayerConfig()
        config.alarms = self.yoto_manager.players[player_id].config.alarms
        config.alarms[alarm].enabled = enable
        await self.hass.async_add_executor_job(
            self.yoto_manager.set_player_config, player_id, config
        )

    async def async_update_card_detail(self, cardId: str) -> None:
        """Get chapter and titles for the card"""
        _LOGGER.debug(f"{DOMAIN} - Updating Card details for:  {cardId}")
        await self.hass.async_add_executor_job(
            self.yoto_manager.update_card_detail, cardId
        )

    async def async_update_library(self) -> None:
        """Update library details."""
        _LOGGER.debug(f"{DOMAIN} - Updating library details")
        await self.hass.async_add_executor_job(self.yoto_manager.update_library)
