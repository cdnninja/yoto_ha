"""Base Entity for Hyundai / Kia Connect integration."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback
from .const import DOMAIN

import asyncio

import logging

_LOGGER = logging.getLogger(__name__)


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
        """Handle updated data from the coordinator."""
        self.schedule_update_ha_state()
        """if not self.enabled:
            return
        else:

            if self.player.card_id and self.player.chapter_key:
                _LOGGER.debug(f"{DOMAIN} - Card ID:  {self.player.card_id} Chapter Key: {self.player.chapter_key}")

                if not (
                    self.player.chapter_key
                    in self.coordinator.yoto_manager.library[self.player.card_id].chapters
                ):
                    _LOGGER.debug(f"{DOMAIN} - updating card details:  {self.player.card_id}")
                    return asyncio.run_coroutine_threadsafe(                    
                        self.coordinator.async_update_card_detail(self.player.card_id),   
                else: 
                    _LOGGER.debug(f"{DOMAIN} - Chapter Details not missing")              
            
"""