"""Coordinator for yoto integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from yoto_api import AuthenticationError, YotoClient

from .const import CONF_TOKEN, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type YotoConfigEntry = ConfigEntry["YotoDataUpdateCoordinator"]


class YotoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: YotoConfigEntry) -> None:
        """Initialize."""
        self.platforms: set[str] = set()
        self.config_entry = config_entry
        self.yoto_client = YotoClient(client_id="KFLTf5PCpTh0yOuDuyQ5C3LEU9PSbult")
        if config_entry.data.get(CONF_TOKEN):
            _LOGGER.debug("Using stored token")
            self.yoto_client.set_refresh_token(config_entry.data.get(CONF_TOKEN))
        else:
            raise ConfigEntryAuthFailed("No token configured")
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict | None:
        """Update data via library. Called by update_coordinator periodically."""
        try:
            await self.async_check_and_refresh_token()
            if self.yoto_client.token.refresh_token != self.config_entry.data.get(
                CONF_TOKEN
            ):
                new_data = dict(self.config_entry.data)
                new_data[CONF_TOKEN] = self.yoto_client.token.refresh_token
                _LOGGER.debug("Storing updated token")
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
        except AuthenticationError as ex:
            _LOGGER.error(f"Authentication error: {ex}")
            raise ConfigEntryAuthFailed

        await self.hass.async_add_executor_job(self.yoto_client.refresh)
        for player_id in list(self.yoto_client.players):
            await self.hass.async_add_executor_job(
                self.yoto_client.update_player_status, player_id
            )
        if len(self.yoto_client.library.keys()) == 0:
            await self.hass.async_add_executor_job(self.yoto_client.update_library)
        if not self.yoto_client.is_mqtt_connected:
            await self.hass.async_add_executor_job(
                self.yoto_client.connect_events,
                list(self.yoto_client.players),
                self.api_callback,
            )
        return self.data

    def api_callback(self, player) -> None:
        """Handle MQTT updates from the library."""
        event = player.last_event
        if event.card_id and event.chapter_key:
            card = self.yoto_client.library.get(event.card_id)
            if (
                card is None
                or not card.chapters
                or event.chapter_key not in card.chapters
            ):
                self.hass.add_job(self.async_update_card_detail, event.card_id)
        self.async_update_listeners()

    async def release(self) -> None:
        """Disconnect from API."""
        await self.hass.async_add_executor_job(self.yoto_client.disconnect_events)

    async def async_update_all(self) -> None:
        """Update yoto data."""
        await self.async_refresh()

    async def async_check_and_refresh_token(self) -> None:
        """Refresh token if needed via library."""
        await self.hass.async_add_executor_job(self.yoto_client.check_and_refresh_token)

    async def async_pause_player(self, player_id: str) -> None:
        """Pause playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_client.pause, player_id)

    async def async_resume_player(self, player_id: str) -> None:
        """Resume playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_client.resume, player_id)

    async def async_stop_player(self, player_id: str) -> None:
        """Stop playback on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_client.stop, player_id)

    async def async_set_player_config(self, player_id: str, **fields: Any) -> None:
        """Update PlayerConfig fields on the device. Pass v3 field names."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            lambda: self.yoto_client.set_player_config(player_id, **fields)
        )
        # The lib doesn't mirror PlayerConfig writes back onto the local
        # player.info.config, so refetch /config to surface the new value
        # before the next 5-minute poll tick.
        await self.hass.async_add_executor_job(
            self.yoto_client.update_player_info, player_id
        )
        self.async_update_listeners()

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
            lambda: self.yoto_client.play_card(
                player_id,
                cardid,
                seconds_in=secondsin,
                cutoff=cutoff,
                chapter_key=str(chapter) if chapter is not None else None,
                track_key=str(trackkey) if trackkey is not None else None,
            )
        )

    async def async_seek(self, player_id: str, position: int) -> None:
        """Seek to a position in the current track."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_client.seek, player_id, position
        )

    async def async_next_track(self, player_id: str) -> None:
        """Skip to the next track."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(self.yoto_client.next_track, player_id)

    async def async_previous_track(self, player_id: str) -> None:
        """Skip to the previous track."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_client.previous_track, player_id
        )

    async def async_set_volume(self, player_id: str, volume: float) -> None:
        """Set player volume level."""
        volume = int(round(volume * 100, 0))
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_client.set_volume, player_id, volume
        )

    async def async_set_sleep_timer(self, player_id: str, time: int) -> None:
        """Set sleep timer on the player."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_client.set_sleep_timer, player_id, int(time)
        )

    async def async_enable_disable_alarm(
        self, player_id: str, alarm: int, enable: bool
    ) -> None:
        """Enable or disable an alarm."""
        await self.async_check_and_refresh_token()
        await self.hass.async_add_executor_job(
            self.yoto_client.set_alarm_enabled, player_id, alarm, enable
        )

    async def async_update_card_detail(self, cardId: str) -> None:
        """Get chapter and titles for the card"""
        _LOGGER.debug(f"{DOMAIN} - Updating Card details for:  {cardId}")
        await self.hass.async_add_executor_job(
            self.yoto_client.update_card_detail, cardId
        )

    async def async_update_library(self) -> None:
        """Update library details."""
        _LOGGER.debug(f"{DOMAIN} - Updating library details")
        await self.hass.async_add_executor_job(self.yoto_client.update_library)
