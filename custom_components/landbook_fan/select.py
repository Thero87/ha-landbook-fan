"""Select: shut-off timer (off, 1-12 hours)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LandbookConfigEntry
from .const import TAG_TIMER, TIMER_OPTIONS
from .entity import LandbookEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LandbookConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([LandbookTimer(entry)])


class LandbookTimer(LandbookEntity, SelectEntity):
    """Fan shut-off timer."""

    _attr_translation_key = "timer"
    _attr_icon = "mdi:timer-outline"
    _attr_options = TIMER_OPTIONS

    def __init__(self, entry: LandbookConfigEntry) -> None:
        super().__init__(entry, "timer")

    @property
    def current_option(self) -> str | None:
        value = self.hub.state.get(TAG_TIMER)
        if value is None:
            return None
        hours = int(value)
        return TIMER_OPTIONS[hours] if 0 <= hours < len(TIMER_OPTIONS) else None

    async def async_select_option(self, option: str) -> None:
        await self.hub.async_write(TAG_TIMER, TIMER_OPTIONS.index(option), is_bool=False)
