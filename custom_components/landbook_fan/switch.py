"""Switches: display light and button beep."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LandbookConfigEntry
from .const import TAG_BEEP, TAG_DISPLAY
from .entity import LandbookEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LandbookConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        [
            LandbookSwitch(entry, "display", TAG_DISPLAY, "mdi:led-on"),
            LandbookSwitch(entry, "beep", TAG_BEEP, "mdi:volume-high"),
        ]
    )


class LandbookSwitch(LandbookEntity, SwitchEntity):
    """A boolean data point on the fan."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: LandbookConfigEntry, key: str, tag: int, icon: str) -> None:
        super().__init__(entry, key)
        self._tag = tag
        self._attr_translation_key = key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        value = self.hub.state.get(self._tag)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hub.async_write(self._tag, True, is_bool=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hub.async_write(self._tag, False, is_bool=True)
