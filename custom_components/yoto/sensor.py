"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

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

    value: Callable[[YotoPlayer], Any]
    always_load: bool = False


SENSOR_DESCRIPTIONS: Final[tuple[YotoSensorEntityDescription, ...]] = (
    YotoSensorEntityDescription(
        key="last_updated_at",
        translation_key="last_updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        always_load=True,
        value=lambda player: max(
            (
                ts
                for ts in (
                    player.info_refreshed_at,
                    player.status_refreshed_at,
                    player.last_event_received_at,
                )
                if ts is not None
            ),
            default=None,
        ),
    ),
    YotoSensorEntityDescription(
        key="battery_level_percentage",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        always_load=True,
        value=lambda player: player.status.battery_level_percentage,
    ),
    YotoSensorEntityDescription(
        key="temperature_celcius",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda player: player.status.temperature_celcius,
    ),
    YotoSensorEntityDescription(
        key="ambient_light_sensor_reading",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        value=lambda player: player.status.ambient_light_sensor_reading,
    ),
    YotoSensorEntityDescription(
        key="wifi_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda player: player.status.wifi_strength,
    ),
    YotoSensorEntityDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value=lambda player: player.status.battery_temperature,
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
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        for description in SENSOR_DESCRIPTIONS:
            if description.always_load or description.value(player) is not None:
                entities.append(YotoSensor(coordinator, description, player))
    async_add_entities(entities)


class YotoSensor(SensorEntity, YotoEntity):
    """Yoto sensor class."""

    entity_description: YotoSensorEntityDescription

    def __init__(
        self,
        coordinator,
        description: YotoSensorEntityDescription,
        player: YotoPlayer,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return self.entity_description.value(self.player)
