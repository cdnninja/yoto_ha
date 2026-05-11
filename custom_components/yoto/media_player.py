"""Media Player for Yoto integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoConfigEntry
from .entity import YotoEntity
from .utils import split_media_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Media Player platform."""
    coordinator = config_entry.runtime_data
    entities: list[YotoMediaPlayer] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        entities.append(YotoMediaPlayer(coordinator, player))
    async_add_entities(entities)


class YotoMediaPlayer(MediaPlayerEntity, YotoEntity):
    """Yoto Media Player class."""

    _attr_has_entity_name = True
    _attr_media_image_remotely_accessible = True
    _attr_name = None
    _attr_translation_key = "Yoto Media Player"

    def __init__(
        self,
        coordinator,
        player: YotoPlayer,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator, player)
        self._id = f"{player.name}"
        self._key = "media_player"
        self._attr_unique_id = f"{DOMAIN}_{player.id}_media_player"
        self._attr_name = None
        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER
        self._currently_playing: dict | None = {}
        self._attr_volume_step = 0.0625
        self._restricted_device: bool = False

    async def async_media_pause(self) -> None:
        """Pause playback."""
        await self.coordinator.async_pause_player(self.player.id)

    async def async_media_play(self) -> None:
        """Play media."""
        await self.coordinator.async_resume_player(self.player.id)

    async def async_media_stop(self) -> None:
        """Stop playback."""
        await self.coordinator.async_stop_player(self.player.id)

    async def async_media_next_track(self) -> None:
        """Skip to next track."""
        await self.coordinator.async_next_track(self.player.id)

    async def async_media_previous_track(self) -> None:
        """Skip to previous track."""
        await self.coordinator.async_previous_track(self.player.id)

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        enqueue: MediaPlayerEnqueue | None = None,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Play media."""
        cardid, chapterid, trackid, time = split_media_id(media_id)
        _LOGGER.debug(
            f"{DOMAIN} - Media requested:  {media_id} Cardid:  {cardid}, chapterid:  {chapterid}, trackid: {trackid}"
        )
        await self.coordinator.async_play_card(
            player_id=self.player.id,
            cardid=cardid,
            chapter=chapterid,
            trackkey=trackid,
            secondsin=int(time),
        )

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        await self.coordinator.async_seek(self.player.id, int(position))

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        await self.coordinator.async_set_volume(self.player.id, volume)

    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""

        _LOGGER.debug(
            f"{DOMAIN} - Browse Media id:  {media_content_id} content type: {media_content_type}"
        )
        await self.coordinator.async_update_library()
        if media_content_id in (None, "library"):
            return await self.async_convert_library_to_browse_media()
        return await self.async_convert_chapter_to_browse_media(media_content_id)

    async def async_convert_library_to_browse_media(self) -> BrowseMedia:
        """Browse library content."""
        children = []

        for item in self.coordinator.yoto_client.library.values():
            children.append(
                BrowseMedia(
                    media_content_id=item.id,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_expand=True,
                    can_play=True,
                    thumbnail=item.cover_image_large,
                )
            )
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

    async def async_convert_chapter_to_browse_media(self, cardid: str) -> BrowseMedia:
        """Browse chapter content for a card."""
        children = []
        _LOGGER.debug(
            f"{DOMAIN} - Chapters:  {self.coordinator.yoto_client.library[cardid].chapters}"
        )
        await self.coordinator.async_update_card_detail(cardid)
        for item in self.coordinator.yoto_client.library[cardid].chapters.values():
            _LOGGER.debug(f"{DOMAIN} - Chapter processing:  {item}")
            children.append(
                BrowseMedia(
                    media_content_id=cardid + "+" + item.key,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_expand=False,
                    can_play=True,
                    thumbnail=item.icon,
                )
            )
        _LOGGER.debug(f"{DOMAIN} - Browse media:  {children}")
        return BrowseMedia(
            media_content_id=cardid,
            media_class=MediaClass.MUSIC,
            media_content_type=MediaType.MUSIC,
            title=self.coordinator.yoto_client.library[cardid].title,
            can_expand=False,
            can_play=True,
            children=children,
            children_media_class=MediaClass.MUSIC,
        )

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
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.SEEK
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the playback state."""
        if not self.player.status.is_online:
            return MediaPlayerState.OFF
        playback_status = self.player.last_event.playback_status
        if playback_status == "paused":
            return MediaPlayerState.PAUSED
        if playback_status == "playing":
            return MediaPlayerState.PLAYING
        if playback_status == "stopped":
            return MediaPlayerState.IDLE
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        """Return the volume level."""
        return self.player.last_event.volume_percentage

    @property
    def media_duration(self) -> int | None:
        """Return the duration of the current media in seconds."""
        return self.player.last_event.track_length

    @property
    def media_position_updated_at(self) -> datetime | None:
        """Return the last time the media position was updated."""
        if self.player.last_event.position is None:
            return None
        return self.player.last_event_received_at

    @property
    def media_artist(self) -> str | None:
        """Return the artist of the current media."""
        card_id = self.player.last_event.card_id
        if card_id and card_id in self.coordinator.yoto_client.library:
            return self.coordinator.yoto_client.library[card_id].author
        return None

    @property
    def media_image_remotely_accessible(self) -> bool:
        """If the image url is remotely accessible."""
        return True

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of the current media."""
        card_id = self.player.last_event.card_id
        if card_id and card_id in self.coordinator.yoto_client.library:
            return self.coordinator.yoto_client.library[card_id].title
        return None

    @property
    def media_image_url(self) -> str | None:
        """Return the image URL of the current media."""
        card_id = self.player.last_event.card_id
        if card_id and card_id in self.coordinator.yoto_client.library:
            return self.coordinator.yoto_client.library[card_id].cover_image_large
        return None

    @property
    def media_position(self) -> int | None:
        """Return the current position of the playback."""
        return self.player.last_event.position

    @property
    def media_content_id(self) -> str | None:
        """Return the current media content ID."""
        event = self.player.last_event
        if event.card_id and event.chapter_key and event.track_key:
            return event.card_id + "+" + event.chapter_key + "+" + event.track_key
        return None

    @property
    def media_title(self) -> str | None:
        """Return the current media title."""
        event = self.player.last_event
        if event.chapter_title == event.track_title:
            return event.chapter_title
        if event.chapter_title and event.track_title:
            return event.chapter_title + " - " + event.track_title
        return event.chapter_title

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        state_attributes: dict[str, Any] = {}
        event = self.player.last_event
        if not event.card_id or not event.chapter_key:
            return state_attributes
        card = self.coordinator.yoto_client.library.get(event.card_id)
        if card is None or not card.chapters:
            return state_attributes
        chapter = card.chapters.get(event.chapter_key)
        if chapter is None:
            return state_attributes
        if chapter.icon:
            state_attributes["media_chapter_icon"] = chapter.icon
        track = (chapter.tracks or {}).get(event.track_key)
        if track is not None and track.icon:
            state_attributes["media_track_icon"] = track.icon
        return state_attributes
