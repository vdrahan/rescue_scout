import argparse
import time

try:
    import RPi.GPIO as GPIO
    import dht11
    import smbus
except ImportError as exc:
    raise RuntimeError(
        "This hardware test script must run on Raspberry Pi with GPIO, dht11, and smbus installed."
    ) from exc

try:
    import gradio as gr
except ImportError:
    gr = None

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


def setup_hardware():
    global red_pwm, green_pwm, blue_pwm, bus, sensor
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    bus = smbus.SMBus(1)
    sensor = dht11.DHT11(pin=DHT_PIN)

    red_pwm = GPIO.PWM(RGB2_R, PWM_FREQUENCY)
    green_pwm = GPIO.PWM(RGB2_G, PWM_FREQUENCY)
    blue_pwm = GPIO.PWM(RGB2_B, PWM_FREQUENCY)
    red_pwm.start(0)
    green_pwm.start(0)
    blue_pwm.start(0)


def cleanup_hardware():
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
    results = []
    results.append(test_buzzer())
    results.append(test_leds())
    results.append(test_rgb_module())
    results.append(test_rgb_led())
    results.append(test_dht11())
    results.append(test_lcd())
    return "\n".join(results)


def run_gradio():
    if gr is None:
        raise RuntimeError("Install gradio to use this interface.")

    def run_buzzer():
        return test_buzzer()

    def run_leds():
        return test_leds()

    def run_rgb_module():
        return test_rgb_module()

    def run_rgb_led():
        return test_rgb_led()

    def run_dht11():
        return test_dht11()

    def run_lcd():
        return test_lcd()

    def run_all():
        return run_all_tests()

    with gr.Blocks() as demo:
        gr.Markdown("# Hardware Test Console")
        output = gr.Textbox(label="Result", lines=10)
        with gr.Row():
            gr.Button("Buzzer").click(run_buzzer, outputs=output)
            gr.Button("Green LEDs").click(run_leds, outputs=output)
            gr.Button("RGB Module").click(run_rgb_module, outputs=output)
        with gr.Row():
            gr.Button("RGB PWM LED").click(run_rgb_led, outputs=output)
            gr.Button("DHT11").click(run_dht11, outputs=output)
            gr.Button("LCD").click(run_lcd, outputs=output)
        gr.Button("Run All Tests").click(run_all, outputs=output)
    demo.launch(server_name="0.0.0.0", server_port=7861)


def main():
    parser = argparse.ArgumentParser(description="Simple hardware test script")
    parser.add_argument("--interface", choices=["cli", "gradio"], default="cli")
    args = parser.parse_args()

    setup_hardware()
    try:
        if args.interface == "gradio":
            run_gradio()
        else:
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
