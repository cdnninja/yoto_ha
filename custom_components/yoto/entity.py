"""Base Entity for Hyundai / Kia Connect integration."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


class YotoConnectEntity(CoordinatorEntity):
    """Class for base entity for Hyundai / Kia Connect integration."""

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
            # model=self.player.model,
            name=self.player.name,
        )
