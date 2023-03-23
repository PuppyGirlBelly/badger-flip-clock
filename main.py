import time
import machine
import badger2040

# We're going to keep the badger on, so slow down the system clock if on battery
badger2040.system_speed(badger2040.SYSTEM_SLOW)

RTC = machine.RTC()
badger = badger2040.Badger2040()
badger.update_speed(badger2040.UPDATE_NORMAL)
badger.font('sans')

TEXT_SCALING = 3
LINE_WIDTH = 10
HALF_HEIGHT = int(badger2040.HEIGHT / 2)
cursors = ["hour", "minute"]
set_clock = False
cursor = 0
last = 0

# Set up the buttons
button_down = machine.Pin(badger2040.BUTTON_DOWN, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_up = machine.Pin(badger2040.BUTTON_UP, machine.Pin.IN, machine.Pin.PULL_DOWN)

button_a = machine.Pin(badger2040.BUTTON_A, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_b = machine.Pin(badger2040.BUTTON_B, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_c = machine.Pin(badger2040.BUTTON_C, machine.Pin.IN, machine.Pin.PULL_DOWN)


# Button handling function
def button(pin):
    global last, set_clock, cursor, hour, minute, last_minute

    time.sleep(0.01)
    if not pin.value():
        return

    if button_a.value() and button_c.value():
        machine.reset()

    adjust = 0
    changed = False

    if pin == button_b:
        set_clock = not set_clock
        changed = True
        if set_clock:
            badger.update_speed(badger2040.UPDATE_TURBO)
        if not set_clock:
            RTC.datetime((1970, 1, 1, 0, hour, minute, 0, 0))
            badger.update_speed(badger2040.UPDATE_NORMAL)

    if set_clock:
        if pin == button_c:
            cursor += 1
            cursor %= len(cursors)

        if pin == button_a:
            cursor -= 1
            cursor %= len(cursors)

        if pin == button_up:
            adjust = 1

        if pin == button_down:
            adjust = -1

        if cursors[cursor] == "hour":
            hour += adjust
            hour %= 12
            if hour == 0:
                hour = 12
        if cursors[cursor] == "minute":
            minute += adjust
            minute %= 60

    if set_clock or changed:
        draw_clock()


# Register the button handling function with the buttons
button_down.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
button_up.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
button_a.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
button_b.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
button_c.irq(trigger=machine.Pin.IRQ_RISING, handler=button)

def x_with_offset(text, x, width, scaling):
    text_width = badger.measure_text(text, scaling)
    text_offset = int(x + (width / 2) - (text_width / 2))
    return text_offset

def draw_clock():

    hour_str = str(hour)
    hour_pos = x_with_offset(hour_str, 9, 134, TEXT_SCALING)
    minute_str = "{:02}".format(minute)
    minute_pos = x_with_offset(minute_str, 155, 134, TEXT_SCALING)

    badger.pen(0)
    badger.clear()
    background = bytearray(int(296*128/8))
    open("background.bin", "r").readinto(background)
    badger.image(background)
    badger.pen(15)
    badger.thickness(LINE_WIDTH)
    badger.text(hour_str, hour_pos, HALF_HEIGHT, TEXT_SCALING)
    badger.text(minute_str, minute_pos, HALF_HEIGHT, TEXT_SCALING)
    badger.pen(0)
    badger.thickness(3)
    badger.line(10, HALF_HEIGHT, 142, HALF_HEIGHT)
    badger.line(155, HALF_HEIGHT, 286, HALF_HEIGHT)

    if set_clock:
        badger.pen(8)
        if cursors[cursor] == "hour":
            badger.line(10, 96, 142, 96)
        if cursors[cursor] == "minute":
            badger.line(155, 96, 286, 96)

    badger.update()

_, _, _, _, hour, minute, _, _ = RTC.datetime()

last_minute = 61

while True:
    if not set_clock:
        _, _, _, _, hour, minute, _, _ = RTC.datetime()
        if minute != last_minute:
            draw_clock()
            last_minute = minute
    time.sleep(1)