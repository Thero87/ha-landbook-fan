"""Base entity for the Landbook fan."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import LandbookConfigEntry
from .const import DOMAIN
from .hub import FanHub


class LandbookEntity(Entity):
    """Entity backed by the shared FanHub (local push)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: LandbookConfigEntry, key: str) -> None:
        self.hub: FanHub = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="OmniBreeze",
            model="Tower Fan (Landbook)",
        )

    @property
    def available(self) -> bool:
        return self.hub.available

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.hub.add_listener(self.async_write_ha_state))
