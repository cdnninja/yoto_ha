"""Light for Yoto integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer, caps_for

from .const import DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class YotoLightEntityDescription(LightEntityDescription):
    """Yoto light entity."""

    value: Callable[[YotoPlayer], str | None]
    setter: Callable[[YotoDataUpdateCoordinator, YotoPlayer, str], Awaitable[None]]


LIGHT_DESCRIPTIONS: Final[tuple[YotoLightEntityDescription, ...]] = (
    YotoLightEntityDescription(
        key="config.day_ambient_colour",
        translation_key="day_ambient_colour",
        value=lambda p: p.info.config.day_ambient_colour,
        setter=lambda c, p, color: c.async_set_player_config(
            p.id, day_ambient_colour=color
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    YotoLightEntityDescription(
        key="config.night_ambient_colour",
        translation_key="night_ambient_colour",
        value=lambda p: p.info.config.night_ambient_colour,
        setter=lambda c, p, color: c.async_set_player_config(
            p.id, night_ambient_colour=color
        ),
        entity_category=EntityCategory.CONFIG,
    ),
)


def _parse_hex(value: str | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    hex_val = value.lstrip("#")
    if len(hex_val) != 6:
        return None
    try:
        return (
            int(hex_val[0:2], 16),
            int(hex_val[2:4], 16),
            int(hex_val[4:6], 16),
        )
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light platform."""
    coordinator = config_entry.runtime_data
    entities: list[YotoLight] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        if not caps_for(player.device).has_ambient_light:
            continue
        for description in LIGHT_DESCRIPTIONS:
            if description.value(player) is not None:
                entities.append(YotoLight(coordinator, description, player))
    async_add_entities(entities)


class YotoLight(LightEntity, YotoEntity):
    """Yoto light entity.

    Yoto stores ambient colour as a single hex RGB string where brightness
    is folded into the channel values (`"#400000"` is a dim red). HA
    prefers a separated model: `rgb_color` normalised so the max channel
    is 255, plus an independent `brightness`. We translate between the
    two on read and write.
    """

    entity_description: YotoLightEntityDescription
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(
        self,
        coordinator,
        description: YotoLightEntityDescription,
        player: YotoPlayer,
    ) -> None:
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"

    @property
    def _rgb_raw(self) -> tuple[int, int, int] | None:
        return _parse_hex(self.entity_description.value(self.player))

    @property
    def is_on(self) -> bool:
        rgb = self._rgb_raw
        return rgb is not None and max(rgb) > 0

    @property
    def brightness(self) -> int | None:
        rgb = self._rgb_raw
        return max(rgb) if rgb is not None else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        rgb = self._rgb_raw
        if rgb is None:
            return None
        peak = max(rgb)
        if peak == 0:
            return (0, 0, 0)
        return tuple(round(c * 255 / peak) for c in rgb)

    async def async_turn_off(self, **kwargs) -> None:
        await self._write("#0")

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
        elif (current := self.rgb_color) is not None:
            r, g, b = current
        else:
            r = g = b = 255
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
        elif current_brightness := self.brightness:
            brightness = current_brightness
        else:
            brightness = 255
        scale = brightness / 255
        hex_color = "#{:02x}{:02x}{:02x}".format(
            round(r * scale),
            round(g * scale),
            round(b * scale),
        )
        await self._write(hex_color)

    async def _write(self, hex_color: str) -> None:
        await self.entity_description.setter(self.coordinator, self.player, hex_color)
        self.async_write_ha_state()
