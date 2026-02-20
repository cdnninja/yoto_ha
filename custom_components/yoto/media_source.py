"""Provide the Yoto Media Source."""

import logging

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .utils import split_media_id

_LOGGER = logging.getLogger(__name__)


class YotoMediaSource(MediaSource):
    """Provide media sources for Yoto Media Player."""

    name: str = "Yoto Media"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize YotoMediaSource."""
        super().__init__(DOMAIN)
        self.hass = hass
        self.coordinator = None

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Provides the URL to play the media."""
        cardid, chapterid, trackid, time = split_media_id(item.identifier)
        if len(self.coordinator.yoto_manager.library[cardid].chapters.keys()) == 0:
            await self.coordinator.async_update_library()
        await self.coordinator.async_update_card_detail(cardid)
        if chapterid is None:
            chapterid = next(iter(self.coordinator.yoto_manager.library[cardid].chapters))
        if trackid is None:
                trackid = next(iter(self.coordinator.yoto_manager.library[cardid].chapters[chapterid].tracks))
        track = (
            self.coordinator.yoto_manager.library[cardid]
            .chapters[chapterid]
            .tracks[trackid]
        )
        if track.format == "aac":
            mime = "audio/aac"
        elif track.format == "mp3":
            mime = "audio/mpeg"
        else:
            _LOGGER.debug(
                f"Unknown format {track.format} for track {track.title}, report this to the developer"
            )
        return PlayMedia(track.trackUrl, mime)

    async def async_browse_media(
        self,
        item: MediaSourceItem | None,
    ) -> BrowseMediaSource:
        """Browse media for Yoto."""
        if self.coordinator is None:
            self.coordinator = next(iter(self.hass.data[DOMAIN].values()))
        if item.identifier is None:
            return await self.async_convert_library_to_browse_media()
        else:
            return await self.async_convert_chapter_to_browse_media(item.identifier)

    async def async_convert_library_to_browse_media(self) -> BrowseMediaSource:
        """Build media source for the library."""
        children = []
        for item in self.coordinator.yoto_manager.library.values():
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=item.id,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_play=True,
                    can_expand=True,
                    thumbnail=item.cover_image_large,
                )
            )
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MUSIC,
            title="Yoto Library",
            can_play=False,
            can_expand=True,
            children=children,
            children_media_class=MediaClass.MUSIC,
        )

    async def async_convert_chapter_to_browse_media(
        self, cardid: str
    ) -> BrowseMediaSource:
        children = []

        if len(self.coordinator.yoto_manager.library[cardid].chapters.keys()) == 0:
            await self.coordinator.async_update_card_detail(cardid)
        for item in self.coordinator.yoto_manager.library[cardid].chapters.values():
            _LOGGER.debug(f"{DOMAIN} - Chapter processing:  {item}")
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=cardid + "-" + item.key,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_expand=False,
                    can_play=True,
                    thumbnail=item.icon,
                )
            )
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=cardid,
            media_class=MediaClass.MUSIC,
            media_content_type=MediaType.MUSIC,
            title=self.coordinator.yoto_manager.library[cardid].title,
            can_expand=False,
            can_play=True,
            children=children,
            children_media_class=MediaClass.MUSIC,
        )

    async def async_convert_track_to_browse_media(
        self, cardid: str, chapterid: str
    ) -> BrowseMediaSource:
        """Build media source for tracks of a chapter."""
        children = []
        if self.coordinator.yoto_manager.library[cardid].chapters[chapterid].tracks:
            for item in (
                self.coordinator.yoto_manager.library[cardid]
                .chapters[chapterid]
                .tracks.values()
            ):
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=cardid + "-" + chapterid + "-" + item.key,
                        media_class=MediaClass.MUSIC,
                        media_content_type=MediaType.MUSIC,
                        title=item.title,
                        can_expand=False,
                        can_play=True,
                        thumbnail=item.icon,
                    )
                )
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=cardid,
            media_class=MediaClass.MUSIC,
            media_content_type=MediaType.MUSIC,
            title=self.coordinator.yoto_manager.library[cardid]
            .chapters[chapterid]
            .title,
            can_expand=False,
            can_play=True,
            children=children,
            children_media_class=MediaClass.MUSIC,
        )


async def async_get_media_source(hass: HomeAssistant) -> YotoMediaSource:
    """Return the Yoto media source instance."""
    return YotoMediaSource(hass)
