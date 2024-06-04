"""Time for Yoto integration."""

from __future__ import annotations

from datetime import time
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.time import (
    TimeEntity,
    TimeEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator
from .entity import YotoEntity

TIME_DESCRIPTIONS: Final[tuple[TimeEntityDescription, ...]] = (
    TimeEntityDescription(
        key="day_mode_time",
        name="Day Mode",
    ),
    TimeEntityDescription(
        key="night_mode_time",
        name="Night Mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up time platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in TIME_DESCRIPTIONS:
            if getattr(player.config, description.key, None) is not None:
                entities.append(YotoTime(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoTime(TimeEntity, YotoEntity):
    def __init__(
        self,
        coordinator: YotoDataUpdateCoordinator,
        description: TimeEntityDescription,
        player: YotoPlayer,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._description.key}"
        self._attr_name = f"{player.name} {self._description.name}"

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return getattr(self.player.config, self._key)

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_time(self.player.id, self._key, value)
        self.async_write_ha_state()
