"""Constants for the Landbook Fan (local) integration.

Data points come from the fan's thing model (productTSL, productKey p11vkW,
"OmniBreeze Tower Fan"), confirmed against live traffic.
"""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "landbook_fan"

CONTROL_PORT: Final = 6607

CONF_AUTH_KEY: Final = "auth_key"

# ---- protocol commands (cmd field) ----
CMD_HELLO: Final = 28722  # p2  app->dev hello
CMD_NONCE: Final = 28723  # p3  dev->app random nonce
CMD_LOGIN: Final = 28724  # p4  app->dev login token
CMD_LOGIN_RESULT: Final = 28725  # p5  dev->app login result (0 = ok)
CMD_WRITE_ACK: Final = 28726  # p6  dev->app write ack
CMD_PING: Final = 28727  # p7
CMD_PONG: Final = 28728  # p8
CMD_HEARTBEAT: Final = 28729  # p9  heartbeat interval
CMD_READ: Final = 17  # read properties (payload = list of 2-byte tag ids)
CMD_WRITE: Final = 19  # write property (payload = TTLV)
CMD_REPORT: Final = 20  # dev->app property report

# ---- data points (TTLV tags) ----
TAG_POWER: Final = 1  # BOOL
TAG_MODE: Final = 2  # ENUM 0..3
TAG_SPEED: Final = 3  # INT 1..5
TAG_OSCILLATION: Final = 5  # BOOL
TAG_BEEP: Final = 13  # BOOL
TAG_DISPLAY: Final = 15  # BOOL
TAG_TEMPERATURE: Final = 21  # INT, degrees F, read-only
TAG_TIMER: Final = 22  # ENUM 0..12 (hours, 0 = off)

READ_TAG_IDS: Final = (
    TAG_POWER,
    TAG_MODE,
    TAG_SPEED,
    TAG_OSCILLATION,
    TAG_BEEP,
    TAG_DISPLAY,
    TAG_TEMPERATURE,
    TAG_TIMER,
)

SPEED_COUNT: Final = 5

MODES: Final = {0: "normal", 1: "natural", 2: "sleep", 3: "auto"}
MODE_IDS: Final = {name: value for value, name in MODES.items()}

TIMER_OPTIONS: Final = ["off"] + [f"{h}h" for h in range(1, 13)]

RECONNECT_DELAY_S: Final = 10
