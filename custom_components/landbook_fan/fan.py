"""Fan entity: power, speed 1-5, preset mode, oscillation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import LandbookConfigEntry
from .const import (
    MODE_IDS,
    MODES,
    SPEED_COUNT,
    TAG_MODE,
    TAG_OSCILLATION,
    TAG_POWER,
    TAG_SPEED,
)
from .entity import LandbookEntity

SPEED_RANGE = (1, SPEED_COUNT)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LandbookConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([LandbookFan(entry)])


class LandbookFan(LandbookEntity, FanEntity):
    """The tower fan."""

    _attr_name = None  # use the device name
    _attr_translation_key = "fan"
    _attr_speed_count = SPEED_COUNT
    _attr_preset_modes = list(MODES.values())
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.OSCILLATE
    )

    def __init__(self, entry: LandbookConfigEntry) -> None:
        super().__init__(entry, "fan")

    @property
    def is_on(self) -> bool | None:
        value = self.hub.state.get(TAG_POWER)
        return None if value is None else bool(value)

    @property
    def percentage(self) -> int | None:
        if not self.is_on:
            return 0
        speed = self.hub.state.get(TAG_SPEED)
        if speed is None:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, int(speed))

    @property
    def preset_mode(self) -> str | None:
        mode = self.hub.state.get(TAG_MODE)
        return None if mode is None else MODES.get(int(mode))

    @property
    def oscillating(self) -> bool | None:
        value = self.hub.state.get(TAG_OSCILLATION)
        return None if value is None else bool(value)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if not self.is_on:
            await self.hub.async_write(TAG_POWER, True, is_bool=True)
        if percentage is not None and percentage > 0:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hub.async_write(TAG_POWER, False, is_bool=True)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        if not self.is_on:
            await self.hub.async_write(TAG_POWER, True, is_bool=True)
        speed = max(1, round(percentage_to_ranged_value(SPEED_RANGE, percentage)))
        await self.hub.async_write(TAG_SPEED, speed, is_bool=False)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.hub.async_write(TAG_MODE, MODE_IDS[preset_mode], is_bool=False)

    async def async_oscillate(self, oscillating: bool) -> None:
        await self.hub.async_write(TAG_OSCILLATION, oscillating, is_bool=True)
