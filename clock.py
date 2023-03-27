import time
import machine
import badger2040

# We're going to keep the badger on, so slow down the system clock if on battery
badger2040.system_speed(badger2040.SYSTEM_SLOW)

TEXT_SCALING = 3
LINE_WIDTH = 10
HALF_HEIGHT = int(badger2040.HEIGHT / 2)

RTC = machine.RTC()
BADGER = badger2040.Badger2040()
BADGER.update_speed(badger2040.UPDATE_NORMAL)
BADGER.font('sans')

# Set up the buttons
BUTTON_DOWN = machine.Pin(badger2040.BUTTON_DOWN, machine.Pin.IN, machine.Pin.PULL_DOWN)
BUTTON_UP = machine.Pin(badger2040.BUTTON_UP, machine.Pin.IN, machine.Pin.PULL_DOWN)
BUTTON_A = machine.Pin(badger2040.BUTTON_A, machine.Pin.IN, machine.Pin.PULL_DOWN)
BUTTON_B = machine.Pin(badger2040.BUTTON_B, machine.Pin.IN, machine.Pin.PULL_DOWN)
BUTTON_C = machine.Pin(badger2040.BUTTON_C, machine.Pin.IN, machine.Pin.PULL_DOWN)

CURSORS = ["hour", "minute"]
set_clock = False
cursor = 0
last = 0

# Button handling function
def button(pin):
    global last, set_clock, cursor, hour, minute, last_minute

    time.sleep(0.01)
    if not pin.value():
        return

    if BUTTON_A.value() and BUTTON_C.value():
        machine.reset()

    adjust = 0
    changed = False

    if pin == BUTTON_B:
        set_clock = not set_clock
        changed = True
        if set_clock:
            BADGER.update_speed(badger2040.UPDATE_TURBO)
        if not set_clock:
            RTC.datetime((1970, 1, 1, 0, hour, minute, 0, 0))
            BADGER.update_speed(badger2040.UPDATE_NORMAL)

    if set_clock:
        if pin == BUTTON_C:
            cursor += 1
            cursor %= len(CURSORS)

        if pin == BUTTON_A:
            cursor -= 1
            cursor %= len(CURSORS)

        if pin == BUTTON_UP:
            adjust = 1

        if pin == BUTTON_DOWN:
            adjust = -1

        if CURSORS[cursor] == "hour":
            hour += adjust
            hour %= 12
            if hour == 0:
                hour = 12
        if CURSORS[cursor] == "minute":
            minute += adjust
            minute %= 60

    if set_clock or changed:
        draw_clock()


# Register the button handling function with the buttons
BUTTON_DOWN.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
BUTTON_UP.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
BUTTON_A.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
BUTTON_B.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
BUTTON_C.irq(trigger=machine.Pin.IRQ_RISING, handler=button)

def x_with_offset(text, x, width, scaling):
    text_width = BADGER.measure_text(text, scaling)
    text_offset = int(x + (width / 2) - (text_width / 2))
    return text_offset

def draw_background():
    background = bytearray(int(296*128/8))
    open("background.bin", "r").readinto(background)
    BADGER.image(background)

def draw_centered_text(str, x_pos, y_pos, width, scaling):
    str_pos = x_with_offset(str, x_pos, width, scaling)
    BADGER.text(str, str_pos, y_pos, scaling)

def draw_clock():
    hour_str = str(hour)
    minute_str = "{:02}".format(minute)

    draw_background()
    BADGER.pen(15)
    BADGER.thickness(LINE_WIDTH)
    draw_centered_text(hour_str, 9, HALF_HEIGHT, 134, TEXT_SCALING)
    draw_centered_text(minute_str, 155, HALF_HEIGHT, 134, TEXT_SCALING)
    BADGER.pen(0)
    BADGER.thickness(3)
    BADGER.line(10, HALF_HEIGHT, 142, HALF_HEIGHT)
    BADGER.line(155, HALF_HEIGHT, 286, HALF_HEIGHT)

    if set_clock:
        BADGER.pen(8)
        if CURSORS[cursor] == "hour":
            BADGER.line(10, 96, 142, 96)
        if CURSORS[cursor] == "minute":
            BADGER.line(155, 96, 286, 96)

    BADGER.update()

_, _, _, _, hour, minute, _, _ = RTC.datetime()
last_minute = 61

while True:
    if not set_clock:
        _, _, _, _, hour, minute, _, _ = RTC.datetime()
        if hour > 12:
            hour %= 12
        if hour == 0:
            hour = 12
        if minute != last_minute:
            draw_clock()
            last_minute = minute
    time.sleep(1)