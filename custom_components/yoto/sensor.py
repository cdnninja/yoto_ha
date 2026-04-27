"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoConfigEntry
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class YotoSensorEntityDescription(SensorEntityDescription):
    """Describe Yoto sensor entity."""

    always_load: bool = False


SENSOR_DESCRIPTIONS: Final[tuple[YotoSensorEntityDescription, ...]] = (
    YotoSensorEntityDescription(
        key="last_updated_at",
        translation_key="last_updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    YotoSensorEntityDescription(
        key="battery_level_percentage",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        always_load=True,
    ),
    YotoSensorEntityDescription(
        key="temperature_celcius",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoSensorEntityDescription(
        key="ambient_light_sensor_reading",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
    ),
    YotoSensorEntityDescription(
        key="wifi_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoSensorEntityDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = config_entry.runtime_data
    entities: list[YotoSensor] = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in SENSOR_DESCRIPTIONS:
            if (
                getattr(player, description.key, None) is not None
                or description.always_load
            ):
                entities.append(YotoSensor(coordinator, description, player))
    async_add_entities(entities)


class YotoSensor(SensorEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: SensorEntityDescription, player: YotoPlayer
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._key}"
        self._attr_state_class = self._description.state_class
        self._attr_device_class = self._description.device_class
        self._attr_entity_category = self._description.entity_category
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )
        self._attr_translation_key = self._description.translation_key

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return getattr(self.player, self._key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value was reported in by the sensor"""

        return self._description.native_unit_of_measurement
