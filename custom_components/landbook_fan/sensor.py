"""Sensor: room temperature reported by the fan."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LandbookConfigEntry
from .const import TAG_TEMPERATURE
from .entity import LandbookEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LandbookConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([LandbookTemperature(entry)])


class LandbookTemperature(LandbookEntity, SensorEntity):
    """Room temperature (the fan reports degrees Fahrenheit)."""

    _attr_translation_key = "temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def __init__(self, entry: LandbookConfigEntry) -> None:
        super().__init__(entry, "temperature")

    @property
    def native_value(self) -> float | None:
        value = self.hub.state.get(TAG_TEMPERATURE)
        return None if value is None else float(value)
