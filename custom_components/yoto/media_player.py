"""Media Player for Yoto integration."""

from __future__ import annotations


from yoto_api import YotoPlayer

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
    MediaPlayerEntityFeature,
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
        self._id = f"{player.name} Media Player"
        # self.data = data
        self._key = "media_player"
        self._attr_unique_id = f"{DOMAIN}_{player.id}_media_player"
        self._attr_name = "Media Player"

        self._currently_playing: dict | None = {}
        self._restricted_device: bool = False

    async def media_pause(self) -> None:
        await self.coordinator.async_pause_player(self.player.id)

    async def media_play(self) -> None:
        await self.coordinator.async_resume_player(self.player.id)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the supported features."""
        return MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.PLAY

    @property
    def state(self) -> MediaPlayerState:
        """Return the playback state."""
        if not self.player.online:
            return MediaPlayerState.OFF
        if self.player.playback_status == "paused":
            return MediaPlayerState.PAUSED
        if self.player.playback_status == "playing":
            return MediaPlayerState.PLAYING
        if self.player.playback_status == "stopped":
            return MediaPlayerState.IDLE
        if self.player.online:
            return MediaPlayerState.ON

    @property
    def volume_level(self) -> float:
        """Return the volume"""
        if self.player.volume:
            return self.player.volume / 10
        else:
            return None

    @property
    def media_duration(self) -> int:
        return self.player.track_length

    @property
    def media_position(self) -> int:
        return self.player.track_position

    @property
    def media_content_id(self) -> str:
        return self.player.card_id

    @property
    def media_title(self) -> str:
        return self.player.chapter_title

    @callback
    def _handle_devices_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.enabled:
            return
        self.async_write_ha_state()
