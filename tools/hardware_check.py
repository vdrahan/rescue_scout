"""Hardware test script.

CLI mode  : direct GPIO access (run with station service STOPPED).
Gradio mode: proxy to the station API (run with station service RUNNING).
"""

import argparse
import time

try:
    import dht11
    import RPi.GPIO as GPIO
    import smbus
    HW_AVAILABLE = True
except ImportError:
    GPIO = None
    dht11 = None
    smbus = None
    HW_AVAILABLE = False

try:
    import gradio as gr
except ImportError:
    gr = None

try:
    import requests as _requests
except ImportError:
    _requests = None

STATION_API = "http://localhost:8001"

BUZZER = 5
RGB1_R = 26
RGB1_G = 16
RGB1_B = 6
LED1 = 23
LED2 = 17
RGB2_R = 22
RGB2_G = 24
RGB2_B = 27
DHT_PIN = 25

PINS = [BUZZER, RGB1_R, RGB1_G, RGB1_B, LED1, LED2, RGB2_R, RGB2_G, RGB2_B]

LCD_ADDR = 0x27
LCD_BACKLIGHT = 0x08
ENABLE = 0b00000100
PWM_FREQUENCY = 1000

red_pwm = None
green_pwm = None
blue_pwm = None
bus = None
sensor = None


# ---------------------------------------------------------------------------
# Station API proxy (used in Gradio mode)
# ---------------------------------------------------------------------------

def _api_test(component: str) -> str:
    """Call the station hardware test API and return a human-readable result."""
    if _requests is None:
        return f"{component}: SKIP — 'requests' package not installed"
    try:
        r = _requests.post(f"{STATION_API}/api/hardware/test/{component}", timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data.get("status", "unknown").upper()
        detail = data.get("detail", "")
        return f"{component}: {status}" + (f" — {detail}" if detail else "")
    except Exception as exc:
        return f"{component}: ERROR — {exc}"


def _api_status() -> str:
    """Return a summary of the station hardware status."""
    if _requests is None:
        return "SKIP — 'requests' package not installed"
    try:
        r = _requests.get(f"{STATION_API}/api/hardware/status", timeout=10)
        r.raise_for_status()
        data = r.json()
        mode = data.get("mode", "?")
        degraded = data.get("degraded", False)
        note = data.get("note", "")
        gas = data.get("gas", {})
        climate = data.get("climate", {})
        lines = [
            f"Station mode: {mode}" + (" (degraded)" if degraded else ""),
        ]
        if note:
            lines.append(f"Note: {note}")
        if gas.get("ppm") is not None:
            lines.append(f"Gas: {gas['ppm']} ppm {'⚠ DANGEROUS' if gas.get('dangerous') else 'OK'}")
        if climate.get("temperature") is not None:
            lines.append(f"Climate: {climate['temperature']}°C / {climate['humidity']}%")
        return "\n".join(lines)
    except Exception as exc:
        return f"Station API unavailable — {exc}"


# ---------------------------------------------------------------------------
# Direct GPIO helpers (CLI mode only — requires station service STOPPED)
# ---------------------------------------------------------------------------

def setup_hardware():
    if not HW_AVAILABLE:
        raise RuntimeError("RPi.GPIO / dht11 / smbus not installed in this environment")
    global red_pwm, green_pwm, blue_pwm, bus, sensor
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    bus = smbus.SMBus(1)
    sensor = dht11.DHT11(pin=DHT_PIN)

    red_pwm = GPIO.PWM(RGB2_R, PWM_FREQUENCY)
    green_pwm = GPIO.PWM(RGB2_G, PWM_FREQUENCY)
    blue_pwm = GPIO.PWM(RGB2_B, PWM_FREQUENCY)
    red_pwm.start(0)
    green_pwm.start(0)
    blue_pwm.start(0)


def cleanup_hardware():
    if not HW_AVAILABLE:
        return
    if red_pwm:
        red_pwm.stop()
    if green_pwm:
        green_pwm.stop()
    if blue_pwm:
        blue_pwm.stop()
    for pin in PINS:
        GPIO.output(pin, GPIO.LOW)
    try:
        lcd_clear()
    except Exception:
        pass
    GPIO.cleanup()


def set_color(r, g, b):
    red_pwm.ChangeDutyCycle(r)
    green_pwm.ChangeDutyCycle(g)
    blue_pwm.ChangeDutyCycle(b)


def beep(on_time, off_time):
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(on_time)
    GPIO.output(BUZZER, GPIO.LOW)
    time.sleep(off_time)


def lcd_write(bits, mode):
    high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    bus.write_byte(LCD_ADDR, high)
    lcd_toggle(high)
    bus.write_byte(LCD_ADDR, low)
    lcd_toggle(low)


def lcd_toggle(bits):
    time.sleep(0.0005)
    bus.write_byte(LCD_ADDR, bits | ENABLE)
    time.sleep(0.0005)
    bus.write_byte(LCD_ADDR, bits & ~ENABLE)
    time.sleep(0.0005)


def lcd_init():
    lcd_write(0x33, 0)
    lcd_write(0x32, 0)
    lcd_write(0x06, 0)
    lcd_write(0x0C, 0)
    lcd_write(0x28, 0)
    lcd_write(0x01, 0)
    time.sleep(0.005)


def lcd_clear():
    lcd_write(0x01, 0)
    time.sleep(0.005)


def lcd_text(text, line):
    if line == 1:
        lcd_write(0x80, 0)
    elif line == 2:
        lcd_write(0xC0, 0)
    text = text.ljust(16)[:16]
    for ch in text:
        lcd_write(ord(ch), 1)


# ---------------------------------------------------------------------------
# Direct GPIO tests (CLI mode)
# ---------------------------------------------------------------------------

def test_buzzer():
    print("Running buzzer test...")
    pattern = [(0.1, 0.05), (0.1, 0.05), (0.2, 0.1)]
    for on_time, off_time in pattern:
        beep(on_time, off_time)
    return "Buzzer: PASS"


def test_leds():
    print("Running LED test...")
    GPIO.output(LED1, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED1, GPIO.LOW)
    GPIO.output(LED2, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED2, GPIO.LOW)
    return "Green LEDs: PASS"


def test_rgb_module():
    print("Running RGB module test...")
    for pin in (RGB1_R, RGB1_G, RGB1_B):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.LOW)
    return "RGB Module: PASS"


def test_rgb_led():
    print("Running RGB PWM LED test...")
    colors = [(0, 100, 0), (100, 0, 0), (0, 0, 100), (100, 100, 0)]
    for r, g, b in colors:
        set_color(r, g, b)
        time.sleep(1)
    set_color(0, 0, 0)
    return "RGB PWM LED: PASS"


def test_dht11():
    print("Running DHT11 test...")
    for _ in range(3):
        result = sensor.read()
        if result.is_valid():
            lcd_clear()
            lcd_text(f"Temp:{result.temperature}C", 1)
            lcd_text(f"Hum:{result.humidity}%", 2)
            time.sleep(2)
            lcd_clear()
            return f"DHT11: PASS ({result.temperature}C, {result.humidity}%)"
        time.sleep(1)
    return "DHT11: FAIL"


def test_lcd():
    print("Running LCD test...")
    lcd_init()
    lcd_clear()
    lcd_text("HARDWARE TEST", 1)
    lcd_text("LCD OK", 2)
    time.sleep(2)
    lcd_clear()
    return "LCD: PASS"


def run_all_tests():
    results = [
        test_buzzer(),
        test_leds(),
        test_rgb_module(),
        test_rgb_led(),
        test_dht11(),
        test_lcd(),
    ]
    return "\n".join(results)


# ---------------------------------------------------------------------------
# Gradio UI (proxies to station API — works while station service is running)
# ---------------------------------------------------------------------------

# Maps Gradio button label → station component id
_COMPONENT_MAP = {
    "Buzzer": "buzzer",
    "Green LEDs": "system_led",
    "RGB Module": "rgb_module",
    "RGB PWM LED": "rgb_status",
    "DHT11 / Climate": "temp_humidity",
    "LCD": "lcd_display",
    "Gas Sensor (MQ-2)": "gas_sensor",
}


def run_gradio():
    if gr is None:
        raise RuntimeError("Install gradio to use this interface: pip install gradio")

    with gr.Blocks(title="Hardware Test Console") as demo:
        gr.Markdown("# Hardware Test Console")
        gr.Markdown(
            "Tests run via the **station API** (`localhost:8000`) — the station service must be running.\n\n"
            "To run direct GPIO tests without the station, use `python test.py --interface cli` "
            "(stop the station service first)."
        )

        with gr.Row():
            status_btn = gr.Button("Get Hardware Status", variant="primary")

        status_out = gr.Textbox(label="Hardware Status", lines=6, interactive=False)
        status_btn.click(fn=_api_status, outputs=status_out)

        gr.Markdown("---\n### Component Tests")
        output = gr.Textbox(label="Test Result", lines=4, interactive=False)

        with gr.Row():
            for label in ("Buzzer", "Green LEDs", "RGB Module"):
                component = _COMPONENT_MAP[label]
                gr.Button(label).click(fn=lambda c=component: _api_test(c), outputs=output)

        with gr.Row():
            for label in ("RGB PWM LED", "DHT11 / Climate", "LCD", "Gas Sensor (MQ-2)"):
                component = _COMPONENT_MAP[label]
                gr.Button(label).click(fn=lambda c=component: _api_test(c), outputs=output)

        def run_all_via_api():
            results = [_api_test(c) for c in _COMPONENT_MAP.values()]
            return "\n".join(results)

        gr.Button("Run All Tests", variant="primary").click(fn=run_all_via_api, outputs=output)

    demo.launch(server_name="0.0.0.0", server_port=7861, inbrowser=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hardware test script")
    parser.add_argument("--interface", choices=["cli", "gradio"], default="gradio")
    args = parser.parse_args()

    if args.interface == "gradio":
        run_gradio()
        return

    # CLI mode: direct GPIO (station service must be stopped)
    if not HW_AVAILABLE:
        print("ERROR: RPi.GPIO / dht11 / smbus not installed. Cannot run CLI hardware tests.")
        return

    try:
        setup_hardware()
    except Exception as exc:
        print(f"ERROR: Hardware setup failed: {exc}")
        print("Hint: stop the station service before running direct GPIO tests.")
        return

    try:
        lcd_init()
        while True:
            print("\nHardware Test Menu")
            print("1 - Buzzer")
            print("2 - Green LEDs")
            print("3 - RGB Module")
            print("4 - RGB PWM LED")
            print("5 - DHT11")
            print("6 - LCD")
            print("7 - Run All Tests")
            print("0 - Exit")
            choice = input("Choose: ")
            if choice == "1":
                print(test_buzzer())
            elif choice == "2":
                print(test_leds())
            elif choice == "3":
                print(test_rgb_module())
            elif choice == "4":
                print(test_rgb_led())
            elif choice == "5":
                print(test_dht11())
            elif choice == "6":
                print(test_lcd())
            elif choice == "7":
                print(run_all_tests())
            elif choice == "0":
                break
            else:
                print("Wrong choice")
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cleanup_hardware()


if __name__ == "__main__":
    main()
