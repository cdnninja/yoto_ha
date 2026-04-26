"""Base entity for Yoto integration."""

from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class YotoEntity(CoordinatorEntity):
    """Base entity for Yoto integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, player):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.player = player

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to use for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.player.id)},
            manufacturer="Yoto",
            model=self.player.device_type,
            name=self.player.name,
            sw_version=self.player.firmware_version,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        # Coordinator's api_callback fires from the paho-mqtt thread, so route
        # the state write through the thread-safe scheduler instead of the
        # default async_write_ha_state.
        self.schedule_update_ha_state()
