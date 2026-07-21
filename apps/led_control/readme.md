# led_control

Configures the Cradlepoint R1900's LEDs by writing directly to their GPIO pins
through the NCOS config store (`control/gpio/<PIN>`).

## How It Works

The R1900 exposes each physical LED as a named GPIO pin, readable at
`status/gpio/<PIN>` and writable at `control/gpio/<PIN>` (0 = off, 1 = on).
`led_control.py` maps friendly names to those pins and provides helpers to
read/set them.

On start, it runs a one-shot test sequence that flashes each mapped LED for
half a second (in turn) so you can confirm GPIO control is working. It then
polls the router every 5 seconds and mirrors real router state onto the
LEDs, only writing a pin when its underlying state actually changes:

| LED(s)                        | Driven by                          | Behavior                              |
|--------------------------------|-------------------------------------|----------------------------------------|
| `modem_green` / `modem_red`    | `status/wan/connection_state`      | Green when connected, red when not     |
| `signal_0`–`signal_3`          | `status/signal_strength_leds`      | All four on/off together (router's own signal-LED decision) |
| `wifi`                          | `control/wlan/enabled`             | On when WLAN is enabled                |

`bluetooth`, `modem_5g_green`, and `attention_red` are mapped but not driven
automatically — call `set_led()` directly for those, or add your own
condition in `update_leds_from_status()`.

## LED Pin Map (R1900)

| Logical name     | GPIO pin        | Description                  |
|-------------------|-----------------|-------------------------------|
| `signal_0`        | `LED_SS_0`      | Signal strength bar 1         |
| `signal_1`        | `LED_SS_1`      | Signal strength bar 2         |
| `signal_2`        | `LED_SS_2`      | Signal strength bar 3         |
| `signal_3`        | `LED_SS_3`      | Signal strength bar 4         |
| `wifi`            | `LED_WIFI`      | WiFi indicator                |
| `bluetooth`       | `LED_BT`        | Bluetooth indicator           |
| `modem_green`     | `MODEM_GRN`     | Modem status (green)          |
| `modem_red`       | `MODEM_RED`     | Modem status (red)            |
| `modem_5g_green`  | `MODEM_5G_GRN`  | 5G modem status (green)       |
| `attention_red`   | `ATTN_RED`      | Attention/fault indicator     |

## Functions

```python
set_led(name, on)     # Turn a named LED on (True) or off (False)
get_led(name)          # Read a named LED's current state (0/1)
set_all_leds(on)       # Set every mapped LED to the same state
led_test_sequence()    # Flash each LED in turn (used on startup)
```

## Usage

Edit `led_control.py` to call `set_led()`/`set_all_leds()` with whatever
trigger logic you need (e.g. based on `status/wan/connection_state`,
`status/signal_strength_leds`, a schedule, or an appdata flag), in place of
or in addition to the startup test sequence.

## Requirements

- Router model: R1900 (pin names above are R1900-specific; other models use
  different `control/gpio`/`status/gpio` pin names — see `cp.get('status/gpio')`
  to list what's available on a different model).
- NCOS SDK / Developer Mode enabled on the router.
- Firmware 7.26 or later.

## Deploying

From the repo root:

```bash
python3 make.py setup            # one-time: create venv, install deps
python3 make.py build led_control # package the app
python3 make.py install          # copy to the router (must be in Dev Mode)
python3 make.py start            # start it
python3 make.py status           # check SDK status
```

Or all at once: `python3 make.py deploy`.

Set `app_name = led_control` (and the router's IP/credentials) in
`sdk_settings.ini` first.
