"""Time entities for Yoto integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import time
from typing import Final

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .entity import YotoEntity


@dataclass(frozen=True, kw_only=True)
class YotoTimeEntityDescription(TimeEntityDescription):
    """Yoto time entity."""

    value: Callable[[YotoPlayer], time | None]
    setter: Callable[[YotoDataUpdateCoordinator, YotoPlayer, time], Awaitable[None]]


TIME_DESCRIPTIONS: Final[tuple[YotoTimeEntityDescription, ...]] = (
    YotoTimeEntityDescription(
        key="day_mode_time",
        translation_key="day_mode_time",
        value=lambda p: p.info.config.day_time,
        setter=lambda c, p, v: c.async_set_player_config(p.id, day_time=v),
        entity_category=EntityCategory.CONFIG,
    ),
    YotoTimeEntityDescription(
        key="night_mode_time",
        translation_key="night_mode_time",
        value=lambda p: p.info.config.night_time,
        setter=lambda c, p, v: c.async_set_player_config(p.id, night_time=v),
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up time platform."""
    coordinator = config_entry.runtime_data
    entities: list[YotoTime] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        for description in TIME_DESCRIPTIONS:
            if description.value(player) is not None:
                entities.append(YotoTime(coordinator, description, player))
    async_add_entities(entities)


class YotoTime(TimeEntity, YotoEntity):
    """Yoto time entity."""

    entity_description: YotoTimeEntityDescription

    def __init__(
        self,
        coordinator,
        description: YotoTimeEntityDescription,
        player: YotoPlayer,
    ) -> None:
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"

    @property
    def native_value(self) -> time | None:
        return self.entity_description.value(self.player)

    async def async_set_value(self, value: time) -> None:
        await self.entity_description.setter(self.coordinator, self.player, value)
        self.async_write_ha_state()
