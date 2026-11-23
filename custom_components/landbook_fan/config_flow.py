"""Config flow: fan IP + auth key, validated by a real local login."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import CONF_AUTH_KEY, DOMAIN
from .protocol import FanAuthError, FanConnection, FanError


async def _validate(host: str, auth_key: str) -> str | None:
    """Return an error key, or None if the fan accepted the login."""
    try:
        if len(base64.b64decode(auth_key, validate=True)) != 16:
            return "invalid_key"
    except (binascii.Error, ValueError):
        return "invalid_key"
    conn = FanConnection(host, auth_key)
    try:
        await conn.connect()
    except FanAuthError:
        return "invalid_auth"
    except (FanError, OSError):
        return "cannot_connect"
    finally:
        await conn.close()
    return None


class LandbookFanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a Landbook fan."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            key = user_input[CONF_AUTH_KEY].strip()
            self._async_abort_entries_match({CONF_HOST: host})
            error = await _validate(host, key)
            if error is None:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or "Tower Fan",
                    data={CONF_HOST: host, CONF_AUTH_KEY: key},
                )
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Tower Fan"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_AUTH_KEY): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=self.add_suggested_values_to_schema(schema, user_input), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the IP or auth key (e.g. after re-pairing the fan)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            key = user_input[CONF_AUTH_KEY].strip()
            error = await _validate(host, key)
            if error is None:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_HOST: host, CONF_AUTH_KEY: key}
                )
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                vol.Required(CONF_AUTH_KEY, default=entry.data[CONF_AUTH_KEY]): str,
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """The fan rejected the stored key: ask for the new one."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            key = user_input[CONF_AUTH_KEY].strip()
            error = await _validate(entry.data[CONF_HOST], key)
            if error is None:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_AUTH_KEY: key})
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_AUTH_KEY): str}),
            errors=errors,
        )
