"""Number entities for Yoto integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class YotoNumberEntityDescription(NumberEntityDescription):
    """Yoto number entity."""

    value: Callable[[YotoPlayer], int | None]
    setter: Callable[[YotoDataUpdateCoordinator, YotoPlayer, int], Awaitable[None]]
    available: Callable[[YotoPlayer], bool] | None = None
    always_load: bool = False


NUMBER_DESCRIPTIONS: Final[tuple[YotoNumberEntityDescription, ...]] = (
    YotoNumberEntityDescription(
        key="config.night_max_volume_limit",
        translation_key="night_max_volume_limit",
        value=lambda p: p.info.config.night_max_volume_limit,
        setter=lambda c, p, v: c.async_set_player_config(
            p.id, night_max_volume_limit=v
        ),
        native_min_value=0,
        native_max_value=16,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    YotoNumberEntityDescription(
        key="config.day_max_volume_limit",
        translation_key="day_max_volume_limit",
        value=lambda p: p.info.config.day_max_volume_limit,
        setter=lambda c, p, v: c.async_set_player_config(p.id, day_max_volume_limit=v),
        native_min_value=0,
        native_max_value=16,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    YotoNumberEntityDescription(
        key="config.day_display_brightness",
        translation_key="day_display_brightness",
        value=lambda p: p.info.config.day_display_brightness,
        setter=lambda c, p, v: c.async_set_player_config(
            p.id, day_display_brightness=v
        ),
        available=lambda p: not p.info.config.day_display_brightness_auto,
        always_load=True,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
    ),
    YotoNumberEntityDescription(
        key="config.night_display_brightness",
        translation_key="night_display_brightness",
        value=lambda p: p.info.config.night_display_brightness,
        setter=lambda c, p, v: c.async_set_player_config(
            p.id, night_display_brightness=v
        ),
        available=lambda p: not p.info.config.night_display_brightness_auto,
        always_load=True,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform."""
    coordinator = config_entry.runtime_data
    entities: list[NumberEntity] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        for description in NUMBER_DESCRIPTIONS:
            if description.always_load or description.value(player) is not None:
                entities.append(YotoNumber(coordinator, description, player))
        entities.append(YotoSleepTimerNumber(coordinator, player))
    async_add_entities(entities)


class YotoNumber(NumberEntity, YotoEntity):
    """Yoto number entity backed by a PlayerConfig field."""

    entity_description: YotoNumberEntityDescription

    def __init__(
        self,
        coordinator,
        description: YotoNumberEntityDescription,
        player: YotoPlayer,
    ) -> None:
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        raw = self.entity_description.value(self.player)
        return float(raw) if raw is not None else None

    @property
    def available(self) -> bool:
        check = self.entity_description.available
        return super().available and (check is None or check(self.player))

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.setter(self.coordinator, self.player, int(value))
        self.async_write_ha_state()


class YotoSleepTimerNumber(NumberEntity, YotoEntity):
    """Number entity exposing the remaining seconds on the sleep timer."""

    _attr_translation_key = "sleep_timer"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_min_value = 0
    _attr_native_max_value = 46500
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, player: YotoPlayer) -> None:
        super().__init__(coordinator, player)
        self._attr_unique_id = f"{DOMAIN}_{player.id}_sleep_timer_seconds_remaining"

    @property
    def native_value(self) -> float | None:
        remaining = self.player.last_event.sleep_timer_seconds
        return float(remaining) if remaining is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_sleep_timer(self.player.id, int(value))
        self.async_write_ha_state()
