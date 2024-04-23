"""Media Player for Yoto integration."""

from __future__ import annotations


from yoto_api import YotoPlayer

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerState

from .const import DOMAIN


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


class YotoMediaPlayer(MediaPlayerEntity):
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
        """Initialize."""
        super().__init__(coordinator, player)
        # self._id = user_id
        # self.data = data

        self._attr_unique_id = f"{DOMAIN}_{player.id}_media_player"

        self._currently_playing: dict | None = {}
        self._restricted_device: bool = False

    @property
    def state(self) -> MediaPlayerState:
        """Return the playback state."""
        if not self.player.is_playing:
            return MediaPlayerState.IDLE
        if self.player.is_playing:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.PAUSED

    @callback
    def _handle_devices_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.enabled:
            return
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.data.devices.async_add_listener(self._handle_devices_update)
        )
