"""Media Player for Yoto integration."""

from __future__ import annotations
from typing import Any

import logging

from yoto_api import YotoPlayer

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
    MediaPlayerEntityFeature,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
    BrowseMedia,
    MediaType,
    MediaClass,
)

from .const import DOMAIN
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


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
        self._attr_name = None
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

    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""

        if media_content_id in (None, "library"):
            children = await self.async_convert_library_to_browse_media()
            return BrowseMedia(
                media_content_id="Root",
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.MUSIC,
                title="Yoto Library",
                can_expand=True,
                can_play=False,
                children=children,
                children_media_class=MediaClass.MUSIC,
            )

    async def async_convert_library_to_browse_media(self) -> list:
        children = []
        for card in self.coordinator.yoto_manager.library.values():
            children.append(
                BrowseMedia(
                    media_content_id=card.id,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=card.title,
                    can_expand=False,
                    can_play=True,
                )
            )
        return children

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the supported features."""
        return (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.BROWSE_MEDIA
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
    def media_artist(self) -> str:
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
            return self.coordinator.yoto_manager.library[
                self.media_content_id
            ].cover_image_large
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

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        state_attributes: dict[str, Any] = {}
        if self.player.card_id and self.player.chapter_key:
            if (
                self.media_content_id in self.coordinator.yoto_manager.library
                and self.coordinator.yoto_manager.library[
                    self.media_content_id
                ].chapters
            ):
                if (
                    self.player.chapter_key
                    in self.coordinator.yoto_manager.library[
                        self.media_content_id
                    ].chapters
                ):
                    if (
                        self.player.track_key
                        in self.coordinator.yoto_manager.library[self.media_content_id]
                        .chapters[self.player.chapter_key]
                        .tracks
                    ):
                        if (
                            self.coordinator.yoto_manager.library[self.media_content_id]
                            .chapters[self.player.chapter_key]
                            .icon
                        ):
                            state_attributes["media_chapter_icon"] = (
                                self.coordinator.yoto_manager.library[
                                    self.media_content_id
                                ]
                                .chapters[self.player.chapter_key]
                                .icon
                            )
                        if (
                            self.coordinator.yoto_manager.library[self.media_content_id]
                            .chapters[self.player.chapter_key]
                            .tracks[self.player.track_key]
                            .icon
                        ):
                            state_attributes["media_track_icon"] = (
                                self.coordinator.yoto_manager.library[
                                    self.media_content_id
                                ]
                                .chapters[self.player.chapter_key]
                                .tracks[self.player.track_key]
                                .icon
                            )
        return state_attributes
