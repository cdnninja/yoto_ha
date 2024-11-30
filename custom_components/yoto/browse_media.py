"""Support for media browsing."""

import logging


from homeassistant.components.media_player import BrowseMedia, MediaClass, MediaType

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_convert_library_to_browse_media(self) -> list:
    children = []

    for item in self.coordinator.yoto_manager.library.values():
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
            BrowseMedia(
                media_content_id=cardid + "-" + item.key,
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
                BrowseMedia(
                    media_content_id=cardid + "-" + chapterid + "-" + item.key,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_expand=False,
                    can_play=True,
                    thumbnail=item.icon,
                )
            )
    return BrowseMedia(
        media_content_id=cardid,
        media_class=MediaClass.MUSIC,
        media_content_type=MediaType.MUSIC,
        title=self.coordinator.yoto_manager.library[cardid].chapters[chapterid].title,
        can_expand=False,
        can_play=True,
        children=children,
        children_media_class=MediaClass.MUSIC,
    )


async def build_item_response(
    self,
    media_content_type: MediaType | str | None = None,
    media_content_id: str | None = None,
) -> BrowseMedia:
    if media_content_id in (None, "library"):
        return await self.async_convert_library_to_browse_media()
    else:
        return await self.async_convert_chapter_to_browse_media(media_content_id)
