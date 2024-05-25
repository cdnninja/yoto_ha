"""Media Player for Yoto integration."""

from __future__ import annotations
from typing import Any

from yoto_api import YotoPlayer

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
)

from .const import DOMAIN
from .entity import YotoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Media Player platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        entities.append(YotoMediaPlayer(coordinator, player))
    async_add_entities(entities)
    return True


class YotoMediaPlayer(MediaPlayerEntity, YotoEntity):
    """Yoto Media Player class."""

    _attr_has_entity_name = True
    _attr_media_image_remotely_accessible = False
    _attr_name = None
    _attr_translation_key = "yoto"

    def __init__(
        self,
        coordinator,
        player: YotoPlayer,
    ) -> None:
        super().__init__(coordinator, player)
        self._id = f"{player.name}"
        # self.data = data
        self._key = "media_player"
        self._attr_unique_id = f"{DOMAIN}_{player.id}_media_player"
        self._attr_name = "Media Player"
        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER
        self._currently_playing: dict | None = {}
        self._attr_volume_step = 0.0625
        self._restricted_device: bool = False

    async def async_media_pause(self) -> None:
        await self.coordinator.async_pause_player(self.player.id)

    async def async_media_play(self) -> None:
        await self.coordinator.async_resume_player(self.player.id)

    async def async_media_stop(self) -> None:
        await self.coordinator.async_stop_player(self.player.id)

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        enqueue: MediaPlayerEnqueue | None = None,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.async_play_card(self.player.id, media_id)

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.async_set_volume(self.player.id, volume)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the supported features."""
        return (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.VOLUME_SET
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the playback state."""

        if self.player.playback_status == "paused":
            return MediaPlayerState.PAUSED
        if self.player.playback_status == "playing":
            return MediaPlayerState.PLAYING
        if self.player.playback_status == "stopped":
            return MediaPlayerState.IDLE
        if not self.player.online:
            return MediaPlayerState.OFF
        if self.player.online:
            return MediaPlayerState.ON

    @property
    def volume_level(self) -> float:
        """Return the volume"""
        if self.player.volume:
            return self.player.volume / 16
        else:
            return None

    @property
    def media_duration(self) -> int:
        return self.player.track_length

    @property
    def media_album_artist(self) -> str:
        if self.media_content_id in self.coordinator.yoto_manager.library:
            return self.coordinator.yoto_manager.library[self.media_content_id].author
        else:
            return None

    @property
    def media_album_name(self) -> str:
        if self.media_content_id in self.coordinator.yoto_manager.library:
            return self.coordinator.yoto_manager.library[self.media_content_id].title
        else:
            return None

    @property
    def media_image_url(self) -> str:
        if self.media_content_id in self.coordinator.yoto_manager.library:
            return self.coordinator.yoto_manager.library[self.media_content_id].cover_image_large
        else:
            return None

    @property
    def media_position(self) -> int:
        return self.player.track_position

    @property
    def media_content_id(self) -> str:
        return self.player.card_id

    @property
    def media_title(self) -> str:
        if self.player.chapter_title == self.player.track_title:
            return self.player.chapter_title
        elif self.player.chapter_title and self.player.track_title:
            return self.player.chapter_title + " - " + self.player.track_title
        else:
            return self.player.chapter_title

    @callback
    def _handle_devices_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.enabled:
            return
        self.async_write_ha_state()
