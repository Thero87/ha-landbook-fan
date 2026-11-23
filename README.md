# Landbook Fan (local) for Home Assistant

Local control of the OmniBreeze tower fan sold at Costco that uses the **Landbook** app
(Quectel/Acceleronix Wi-Fi module, productKey `p11vkW`). HA talks to the fan directly on
your LAN (TCP 6607, AES-encrypted). Nothing goes through the cloud at runtime.

Protocol work builds on [ha-oukitel-powerstation](https://github.com/rzemykers/ha-oukitel-powerstation)
(MIT), which runs on the same Quectel platform.

## Entities
| Entity | What it does |
|---|---|
| Fan | On/off, speed 1–5 (20% steps), presets Normal / Natural / Sleep / Auto, oscillation |
| Switch: Display light | Turns the front display LEDs on/off |
| Switch: Button beep | Turns the button beep on/off |
| Sensor: Room temperature | The fan's built-in thermometer (°F; HA converts if you use °C) |
| Select: Shut-off timer | Off, 1–12 hours |

## Install
1. Copy `custom_components/landbook_fan` into your HA config folder, giving you
   `/config/custom_components/landbook_fan/`.
2. Restart Home Assistant.
3. **Settings → Devices & services → Add integration → "Landbook Fan (local)"**.
4. Enter the fan's IP and its **auth key**.

## Things to know
- **Give the fan a fixed IP** (a DHCP reservation in your router). The integration connects to that IP.
- **The auth key changes whenever you re-pair the fan in Landbook.** HA will then show a
  "re-authenticate" prompt, where you paste the new key. You get the key from the Landbook
  cloud's device list (`authKey` field), for example by proxying the app with mitmproxy.
- Landbook keeps working alongside HA.
