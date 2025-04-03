"""Provide the Yoto Media Source."""

import logging


from homeassistant.components.media_source import (
    MediaSource,
    BrowseMediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant
from homeassistant.components.media_player import MediaClass, MediaType

from .const import DOMAIN
from .utils import split_media_id

_LOGGER = logging.getLogger(__name__)


class YotoMediaSource(MediaSource):
    """Provide media sources for Yoto Media Player."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize YotoMediaSource."""
        super().__init__(DOMAIN)
        self.hass = hass
        self.coordinator = None

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Provides the URL to play the media."""
        _LOGGER.debug(f"{DOMAIN} - Resolve media: {item.identifier}")
        cardid, chapterid, trackid, time = split_media_id(item.identifier)
        if trackid is None:
            if chapterid is not None:
                trackid = chapterid
            else:
                trackid = 1
        if chapterid is None:
            if trackid is not None:
                chapterid = trackid
            else:
                chapterid = 1
        track = (
            self.coordinator.yoto_manager.library[cardid]
            .chapters[chapterid]
            .tracks[trackid]
        )
        if track.format == "aac":
            mime = "audio/aac"
        elif track.format == "mp3":
            mime = "audio/mpeg"
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

    async def async_convert_library_to_browse_media(self) -> list:
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

    async def async_convert_chapter_to_browse_media(self, cardid: str) -> list:
        children = []
        _LOGGER.debug(
            f"{DOMAIN} - Chapters:  {self.coordinator.yoto_manager.library[cardid].chapters}"
        )
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
        _LOGGER.debug(f"{DOMAIN} - Browse media:  {children}")
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
    ) -> list:
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
