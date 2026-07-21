# Ericsson Cradlepoint SDK Application
# led_control - Configure the R1900's LEDs by writing to their GPIO pins.
import cp
import time

# R1900 LED pin map: logical name -> control/gpio pin name.
# Confirmed against the router's status/gpio pin list (Cradlepoint GPIO Reference, R1900).
R1900_LEDS = {
    'signal_0': 'LED_SS_0',    # Signal strength bar 1
    'signal_1': 'LED_SS_1',    # Signal strength bar 2
    'signal_2': 'LED_SS_2',    # Signal strength bar 3
    'signal_3': 'LED_SS_3',    # Signal strength bar 4
    'wifi': 'LED_WIFI',
    'bluetooth': 'LED_BT',
    'modem_green': 'MODEM_GRN',
    'modem_red': 'MODEM_RED',
    'modem_5g_green': 'MODEM_5G_GRN',
    'attention_red': 'ATTN_RED',
}


def set_led(name, on):
    """Set an R1900 LED on or off by its logical name."""
    pin = R1900_LEDS.get(name)
    if pin is None:
        cp.log(f'Unknown LED name: {name}. Valid names: {list(R1900_LEDS)}')
        return False
    result = cp.put(f'control/gpio/{pin}', 1 if on else 0)
    if result is None:
        cp.log(f'Failed to set {name} ({pin})')
        return False
    cp.log(f'Set {name} ({pin}) -> {"ON" if on else "OFF"}')
    return True


def get_led(name):
    """Read the current state of an R1900 LED by its logical name."""
    pin = R1900_LEDS.get(name)
    if pin is None:
        cp.log(f'Unknown LED name: {name}. Valid names: {list(R1900_LEDS)}')
        return None
    return cp.get(f'status/gpio/{pin}')


def set_all_leds(on):
    """Set every mapped R1900 LED to the same state."""
    for name in R1900_LEDS:
        set_led(name, on)


def led_test_sequence():
    """Flash each mapped LED on then off, one at a time, to confirm GPIO control works."""
    cp.log('Running LED test sequence...')
    for name in R1900_LEDS:
        set_led(name, True)
        time.sleep(0.5)
        set_led(name, False)
    cp.log('LED test sequence complete.')


def update_leds_from_status(previous):
    """Poll router status and mirror it onto the LEDs. Returns the new state dict.

    - modem_green / modem_red: WAN connection state.
    - signal_0..3: router's own signal-strength-LED decision (all four bars
      together, since status/signal_strength_leds is a single on/off value).
    - wifi: WLAN enabled state.
    """
    current = {}

    connected = cp.get('status/wan/connection_state') == 'connected'
    current['connected'] = connected
    if previous.get('connected') != connected:
        set_led('modem_green', connected)
        set_led('modem_red', not connected)

    signal_on = cp.get('status/signal_strength_leds') == 'on'
    current['signal_on'] = signal_on
    if previous.get('signal_on') != signal_on:
        for name in ('signal_0', 'signal_1', 'signal_2', 'signal_3'):
            set_led(name, signal_on)

    wifi_enabled = bool(cp.get('control/wlan/enabled'))
    current['wifi_enabled'] = wifi_enabled
    if previous.get('wifi_enabled') != wifi_enabled:
        set_led('wifi', wifi_enabled)

    return current


cp.log('Starting led_control...')
led_test_sequence()

state = {}
while True:
    try:
        state = update_leds_from_status(state)
    except Exception as e:
        cp.log(f'Error updating LEDs: {e}')
    time.sleep(5)
