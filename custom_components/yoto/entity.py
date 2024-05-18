"""Base Entity for Hyundai / Kia Connect integration."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback
from .const import DOMAIN


class YotoEntity(CoordinatorEntity):
    """Class for base entity for Yoto integration."""

    def __init__(self, coordinator, player):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.player = player

    @property
    def device_info(self):
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
        self.schedule_update_ha_state()
