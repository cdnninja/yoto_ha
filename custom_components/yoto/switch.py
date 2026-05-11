"""Switch entities for Yoto integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class YotoSwitchEntityDescription(SwitchEntityDescription):
    """Yoto switch entity."""

    value: Callable[[YotoPlayer], bool | None]
    setter: Callable[
        [YotoDataUpdateCoordinator, YotoPlayer, bool], Awaitable[None]
    ]


# Default brightness applied when the user turns off auto mode — Yoto's
# API doesn't keep a "previous manual value", so we have to pick one.
_DEFAULT_MANUAL_BRIGHTNESS = 100


async def _set_brightness_auto(
    coordinator: YotoDataUpdateCoordinator,
    player: YotoPlayer,
    field_auto: str,
    field_value: str,
    enabled: bool,
) -> None:
    if enabled:
        await coordinator.async_set_player_config(player.id, **{field_auto: True})
    else:
        current = getattr(player.info.config, field_value)
        await coordinator.async_set_player_config(
            player.id, **{field_value: current or _DEFAULT_MANUAL_BRIGHTNESS}
        )


SWITCH_DESCRIPTIONS: Final[tuple[YotoSwitchEntityDescription, ...]] = (
    YotoSwitchEntityDescription(
        key="night_display_brightness",
        translation_key="night_display_brightness",
        value=lambda p: p.info.config.night_display_brightness_auto,
        setter=lambda c, p, on: _set_brightness_auto(
            c, p, "night_display_brightness_auto", "night_display_brightness", on
        ),
        entity_category=EntityCategory.CONFIG,
    ),
    YotoSwitchEntityDescription(
        key="day_display_brightness",
        translation_key="day_display_brightness",
        value=lambda p: p.info.config.day_display_brightness_auto,
        setter=lambda c, p, on: _set_brightness_auto(
            c, p, "day_display_brightness_auto", "day_display_brightness", on
        ),
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch platform."""
    coordinator = config_entry.runtime_data
    entities: list[SwitchEntity] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        for description in SWITCH_DESCRIPTIONS:
            entities.append(YotoSwitch(coordinator, description, player))
        entities.append(YotoEndOfTrackSleepSwitch(coordinator, player))
        for index in range(len(player.info.config.alarms)):
            entities.append(YotoAlarmSwitch(coordinator, player, index))
    async_add_entities(entities)


class YotoSwitch(SwitchEntity, YotoEntity):
    """Yoto switch backed by a PlayerConfig boolean field."""

    entity_description: YotoSwitchEntityDescription

    def __init__(
        self,
        coordinator,
        description: YotoSwitchEntityDescription,
        player: YotoPlayer,
    ) -> None:
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_switch_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value(self.player)

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.setter(self.coordinator, self.player, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.setter(self.coordinator, self.player, False)
        self.async_write_ha_state()


class YotoEndOfTrackSleepSwitch(SwitchEntity, YotoEntity):
    """Synthetic switch: ON when the sleep timer is set to expire at the
    end of the current track (give or take a few seconds)."""

    _attr_translation_key = "end_of_track_sleep"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, player: YotoPlayer) -> None:
        super().__init__(coordinator, player)
        self._attr_unique_id = f"{DOMAIN}_{player.id}_switch_end_of_track_sleep"

    @property
    def is_on(self) -> bool:
        event = self.player.last_event
        if (
            event.track_length is None
            or event.position is None
            or event.sleep_timer_seconds is None
        ):
            return False
        seconds_to_end = event.track_length - event.position
        return abs(event.sleep_timer_seconds - seconds_to_end) <= 5

    async def async_turn_on(self, **kwargs) -> None:
        event = self.player.last_event
        if event.track_length is not None and event.position is not None:
            seconds_to_end = event.track_length - event.position
            await self.coordinator.async_set_sleep_timer(
                self.player.id, seconds_to_end
            )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_sleep_timer(self.player.id, 0)
        self.async_write_ha_state()


class YotoAlarmSwitch(SwitchEntity, YotoEntity):
    """Switch backing one alarm slot (enable / disable)."""

    _attr_translation_key = "alarm"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, player: YotoPlayer, index: int) -> None:
        super().__init__(coordinator, player)
        self._index = index
        self._attr_unique_id = f"{DOMAIN}_{player.id}_switch_alarms[{index}]"
        self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def is_on(self) -> bool | None:
        alarms = self.player.info.config.alarms
        if 0 <= self._index < len(alarms):
            return alarms[self._index].enabled
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_enable_disable_alarm(
            self.player.id, self._index, True
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_enable_disable_alarm(
            self.player.id, self._index, False
        )
        self.async_write_ha_state()
