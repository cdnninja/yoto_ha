"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .entity import YotoEntity
from .utils import parse_key

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: Final[tuple[SwitchEntityDescription, ...]] = (
    SwitchEntityDescription(
        key="night_display_brightness",
        name="Night Auto Display Brightness",
        icon="mdi:brightness-auto",
    ),
    SwitchEntityDescription(
        key="day_display_brightness",
        name="Day Auto Display Brightness",
        icon="mdi:brightness-auto",
    ),
    SwitchEntityDescription(
        key="end_of_track_sleep",
        name="End of Track Sleep",
        icon="mdi:sleep",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for index in range(len(player.config.alarms)):
            alarm_description = SwitchEntityDescription(
                key="alarms[" + str(index) + "]",
                name="Alarm " + str(index + 1),
                icon="mdi:alarm",
            )
            entities.append(YotoSwitch(coordinator, alarm_description, player))

        for description in SENSOR_DESCRIPTIONS:
            if getattr(player.config, description.key, None) is not None:
                entities.append(YotoSwitch(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoSwitch(SwitchEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: SwitchEntityDescription, player: YotoPlayer
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_switch_{self._key}"
        if self._key.startswith("alarms"):
            self._attribute, self._index = parse_key(self._key)
        self._attr_icon = self._description.icon
        self._attr_name = f"{player.name} {self._description.name}"

    @property
    def is_on(self) -> bool | None:
        """Return the entity value to represent the entity state."""
        if (
            self._key == "night_display_brightness"
            or self._key == "day_display_brightness"
        ):
            if getattr(self.player.config, self._key) == "auto":
                return True
            else:
                return False
        elif self._key == "end_of_track_sleep":
            seconds_to_end = self.player.track_length - self.player.track_position
            if abs(self.player.sleep_timer_seconds_remaining - seconds_to_end) <= 5:
                return True
            else:
                return False
        elif self._key.startswith("alarms"):
            return getattr(self.player.config, self._attribute)[self._index].enabled

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        if (
            self._key == "night_display_brightness"
            or self._key == "day_display_brightness"
        ):
            await self.coordinator.async_set_brightness(self.player.id, self._key, "0")
        elif self._key == "end_of_track_sleep":
            await self.coordinator.async_set_sleep_timer(self.player.id, 0)
        elif self._key.startswith("alarms"):
            await self.coordinator.async_enable_disable_alarm(
                self.player.id, self._index, False
            )
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity off."""
        if (
            self._key == "night_display_brightness"
            or self._key == "day_display_brightness"
        ):
            await self.coordinator.async_set_brightness(
                self.player.id, self._key, "auto"
            )
        elif self._key == "end_of_track_sleep":
            seconds_to_end = self.player.track_length - self.player.track_position
            await self.coordinator.async_set_sleep_timer(self.player.id, seconds_to_end)
        elif self._key.startswith("alarms"):
            await self.coordinator.async_enable_disable_alarm(
                self.player.id, self._index, True
            )
        self.async_write_ha_state()
