"""Connection manager: keeps one local session to the fan alive and fans out state."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import RECONNECT_DELAY_S
from .protocol import FanAuthError, FanConnection, FanError

_LOGGER = logging.getLogger(__name__)


class FanHub:
    """Owns the TCP session, reconnects on failure, and holds the latest state."""

    def __init__(self, hass: HomeAssistant, host: str, auth_key: str) -> None:
        self.hass = hass
        self.host = host
        self._auth_key = auth_key
        self.state: dict[int, object] = {}
        self.available = False
        self.auth_failed = False
        self._conn: FanConnection | None = None
        self._task: asyncio.Task | None = None
        self._listeners: list[Callable[[], None]] = []
        self._first_state = asyncio.Event()
        self._connected = asyncio.Event()
        self._kick = asyncio.Event()

    # --- listeners ---
    @callback
    def add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(cb)

        def remove() -> None:
            with contextlib.suppress(ValueError):
                self._listeners.remove(cb)

        return remove

    @callback
    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    @callback
    def _on_report(self, report: dict[int, object]) -> None:
        self.state.update(report)
        self._first_state.set()
        self._notify()

    def _set_available(self, value: bool) -> None:
        if value:
            self._connected.set()
        else:
            self._connected.clear()
        if self.available != value:
            self.available = value
            self.hass.loop.call_soon_threadsafe(self._notify)

    # --- lifecycle ---
    async def async_start(self) -> None:
        """Connect once (so setup can fail fast), then keep the session alive in the background."""
        conn = FanConnection(self.host, self._auth_key, on_report=self._on_report)
        await conn.connect()  # raises FanError / FanAuthError
        self._conn = conn
        self._set_available(True)
        # Start the read loop first so the snapshot reply below is actually consumed.
        self._task = self.hass.async_create_background_task(
            self._run(), name=f"landbook_fan {self.host}"
        )
        await conn.subscribe_and_read()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._first_state.wait(), 5)

    async def _run(self) -> None:
        while True:
            try:
                if self._conn is None:
                    conn = FanConnection(self.host, self._auth_key, on_report=self._on_report)
                    await conn.connect()
                    self._conn = conn
                    await conn.subscribe_and_read()
                    self.auth_failed = False
                    self._set_available(True)
                    _LOGGER.info("Reconnected to fan at %s", self.host)
                await self._conn.listen()
            except asyncio.CancelledError:
                raise
            except FanAuthError as err:
                self.auth_failed = True
                _LOGGER.error(
                    "Fan at %s rejected the auth key (%s). If you re-paired the fan in "
                    "Landbook, its key changed: reconfigure the integration with the new one",
                    self.host,
                    err,
                )
            except (FanError, OSError) as err:
                if self.available:
                    _LOGGER.warning("Lost connection to fan at %s (%s); retrying", self.host, err)
                else:
                    _LOGGER.debug("Fan at %s still unreachable: %s", self.host, err)
            self._set_available(False)
            if self._conn is not None:
                with contextlib.suppress(Exception):
                    await self._conn.close()
                self._conn = None
            # Wait before retrying, but retry at once if a command needs the fan.
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._kick.wait(), RECONNECT_DELAY_S * (6 if self.auth_failed else 1)
                )
            self._kick.clear()

    async def async_stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._task
            self._task = None
        if self._conn is not None:
            with contextlib.suppress(Exception):
                await self._conn.close()
            self._conn = None

    # --- commands ---
    async def _drop_connection(self) -> None:
        """Kill a socket we know is dead so the run loop reconnects right away."""
        self._set_available(False)
        conn = self._conn
        if conn is not None:
            with contextlib.suppress(Exception):
                await conn.close()  # makes listen() fail -> _run reconnects
        self._kick.set()

    async def async_write(self, tag: int, value: object, *, is_bool: bool) -> None:
        for attempt in (1, 2):
            if not self._connected.is_set():
                # e.g. the fan was just power-cycled: give the reconnect a moment
                self._kick.set()
                try:
                    await asyncio.wait_for(self._connected.wait(), 20)
                except TimeoutError as err:
                    raise HomeAssistantError("The fan is not reachable right now") from err
            conn = self._conn
            if conn is None:
                continue
            try:
                await conn.async_set(tag, value, is_bool=is_bool)
                break
            except FanError as err:
                _LOGGER.debug("Write failed (%s); reconnecting and retrying", err)
                await self._drop_connection()
                if attempt == 2:
                    raise HomeAssistantError(f"Could not send command to the fan: {err}") from err
        else:
            raise HomeAssistantError("The fan is not reachable right now")
        # Optimistic update; the fan's own report follows within a second.
        self.state[tag] = bool(value) if is_bool else int(value)
        self._notify()
