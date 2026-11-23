"""Landbook Fan (local): control Quectel/Acceleronix-based fans over the LAN."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import CONF_AUTH_KEY
from .hub import FanHub
from .protocol import FanAuthError, FanError

PLATFORMS: list[Platform] = [Platform.FAN, Platform.SWITCH, Platform.SENSOR, Platform.SELECT]

type LandbookConfigEntry = ConfigEntry[FanHub]


async def async_setup_entry(hass: HomeAssistant, entry: LandbookConfigEntry) -> bool:
    hub = FanHub(hass, entry.data[CONF_HOST], entry.data[CONF_AUTH_KEY])
    try:
        await hub.async_start()
    except FanAuthError as err:
        raise ConfigEntryAuthFailed(
            "The fan rejected the auth key. It changes when the fan is re-paired in Landbook."
        ) from err
    except (FanError, OSError) as err:
        raise ConfigEntryNotReady(f"Cannot reach the fan at {entry.data[CONF_HOST]}: {err}") from err

    entry.runtime_data = hub
    entry.async_on_unload(hub.async_stop)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LandbookConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
