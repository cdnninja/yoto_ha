"""Media Source for Yoto integration."""

import logging


from homeassistant.core import HomeAssistant

from homeassistant.components.media_player import MediaClass

from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_media_source(hass: HomeAssistant):
    """Set up Yoto media source."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    return YotoSource(hass, client)


@callback
def async_parse_identifier(
    item: MediaSourceItem,
) -> tuple[str, str, str]:
    """Parse identifier."""
    identifier = item.identifier or ""
    start = ["", "", ""]
    items = identifier.lstrip("/").split("~~", 2)
    return tuple(items + start[len(items) :])  # type: ignore[return-value]


@dataclass
class YotoMediaItem:
    """Represents a track"""

    caption: str
    thumbnail: str
    uri: str
    media_class: str


class YotoSource(MediaSource):
    """Provide Yoto tracks as media sources."""

    name: str = "Yoto Track Media"

    def __init__(self, hass: HomeAssistant, client: YotoClient) -> None:
        """Initialize Xbox source."""
        super().__init__(DOMAIN)

        self.hass: HomeAssistant = hass
        self.yotoManager: YotoManager = client

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        _, category, url = async_parse_identifier(item)
        kind = category.split("#", 1)[1]
        return PlayMedia(url, MIME_TYPE_MAP[kind])

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return media."""
        title, category, _ = async_parse_identifier(item)

        if not title:
            return await self._build_game_library()

        if not category:
            return _build_categories(title)

        return await self._build_media_items(title, category)

    async def _build_game_library(self) -> BrowseMediaSource:
        """Display installed games across all consoles."""
        apps = await self.client.smartglass.get_installed_apps()
        games = {
            game.one_store_product_id: game
            for game in apps.result
            if game.is_game and game.title_id
        }

        app_details = await self.client.catalog.get_products(
            games.keys(),
            FieldsTemplate.BROWSE,
        )

        images = {
            prod.product_id: prod.localized_properties[0].images
            for prod in app_details.products
        }

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="",
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Yoto Track",
            can_play=False,
            can_expand=True,
            children=[_build_game_item(game, images) for game in games.values()],
            children_media_class=MediaClass.GAME,
        )

    async def _build_media_items(self, title, category) -> BrowseMediaSource:
        """Fetch requested gameclip/screenshot media."""
        title_id, _, thumbnail = title.split("#", 2)
        owner, kind = category.split("#", 1)

        items: list[YotoMediaItem] = []
        with suppress(ValidationError):  # Unexpected API response
            if kind == "gameclips":
                if owner == "my":
                    response: GameclipsResponse = (
                        await self.client.gameclips.get_recent_clips_by_xuid(
                            self.client.xuid, title_id
                        )
                    )
                elif owner == "community":
                    response: GameclipsResponse = await self.client.gameclips.get_recent_community_clips_by_title_id(
                        title_id
                    )
                else:
                    return None
                items = [
                    YotoMediaItem(
                        item.user_caption
                        or dt_util.as_local(
                            dt_util.parse_datetime(item.date_recorded)
                        ).strftime("%b. %d, %Y %I:%M %p"),
                        item.thumbnails[0].uri,
                        item.game_clip_uris[0].uri,
                        MediaClass.VIDEO,
                    )
                    for item in response.game_clips
                ]
            elif kind == "screenshots":
                if owner == "my":
                    response: ScreenshotResponse = (
                        await self.client.screenshots.get_recent_screenshots_by_xuid(
                            self.client.xuid, title_id
                        )
                    )
                elif owner == "community":
                    response: ScreenshotResponse = await self.client.screenshots.get_recent_community_screenshots_by_title_id(
                        title_id
                    )
                else:
                    return None
                items = [
                    YotoMediaItem(
                        item.user_caption
                        or dt_util.as_local(item.date_taken).strftime(
                            "%b. %d, %Y %I:%M%p"
                        ),
                        item.thumbnails[0].uri,
                        item.screenshot_uris[0].uri,
                        MediaClass.IMAGE,
                    )
                    for item in response.screenshots
                ]

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{title}~~{category}",
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title=f"{owner.title()} {kind.title()}",
            can_play=False,
            can_expand=True,
            children=[_build_media_item(title, category, item) for item in items],
            children_media_class=MEDIA_CLASS_MAP[kind],
            thumbnail=thumbnail,
        )


def _build_game_item(
    item: InstalledPackage, images: dict[str, list[Image]]
) -> BrowseMediaSource:
    """Build individual game."""
    thumbnail = ""
    image = _find_media_image(images.get(item.one_store_product_id, []))
    if image is not None:
        thumbnail = image.uri
        if thumbnail[0] == "/":
            thumbnail = f"https:{thumbnail}"

    return BrowseMediaSource(
        domain=DOMAIN,
        identifier=f"{item.title_id}#{item.name}#{thumbnail}",
        media_class=MediaClass.GAME,
        media_content_type="",
        title=item.name,
        can_play=False,
        can_expand=True,
        children_media_class=MediaClass.DIRECTORY,
        thumbnail=thumbnail,
    )


def _build_categories(title) -> BrowseMediaSource:
    """Build base categories for Xbox media."""
    _, name, thumbnail = title.split("#", 2)
    base = BrowseMediaSource(
        domain=DOMAIN,
        identifier=f"{title}",
        media_class=MediaClass.GAME,
        media_content_type="",
        title=name,
        can_play=False,
        can_expand=True,
        children=[],
        children_media_class=MediaClass.DIRECTORY,
        thumbnail=thumbnail,
    )

    owners = ["my", "community"]
    kinds = ["gameclips", "screenshots"]
    for owner in owners:
        for kind in kinds:
            base.children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{title}~~{owner}#{kind}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type="",
                    title=f"{owner.title()} {kind.title()}",
                    can_play=False,
                    can_expand=True,
                    children_media_class=MEDIA_CLASS_MAP[kind],
                )
            )

    return base


def _build_media_item(
    title: str, category: str, item: YotoMediaItem
) -> BrowseMediaSource:
    """Build individual media item."""
    kind = category.split("#", 1)[1]
    return BrowseMediaSource(
        domain=DOMAIN,
        identifier=f"{title}~~{category}~~{item.uri}",
        media_class=item.media_class,
        media_content_type=MIME_TYPE_MAP[kind],
        title=item.caption,
        can_play=True,
        can_expand=False,
        thumbnail=item.thumbnail,
    )
