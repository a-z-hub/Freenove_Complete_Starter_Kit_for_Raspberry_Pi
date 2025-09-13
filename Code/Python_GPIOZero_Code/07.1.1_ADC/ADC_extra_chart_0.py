#!/usr/bin/env python3
import curses
import time
from collections import deque
from ADCDevice import *

adc = ADCDevice()

def setup():
    global adc
    if adc.detectI2C(0x48):
        adc = PCF8591()
    elif adc.detectI2C(0x4b):
        adc = ADS7830()
    else:
        print("No correct I2C address found.\nUse 'i2cdetect -y 1' to check.\n")
        exit(1)

def read_voltage():
    value = adc.analogRead(0)           # 0..255
    voltage = value / 255.0 * 3.3       # 0..3.3V
    return voltage

def draw_chart(stdscr, values, vmin=0.0, vmax=3.3, title="CH0 Voltage, V"):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    left_pad = 8
    right_pad = 1
    top_pad = 1
    bottom_pad = 2

    plot_w = max(1, w - left_pad - right_pad)
    plot_h = max(1, h - top_pad - bottom_pad)

    try:
        stdscr.addstr(0, 2, f"{title}".ljust(max(0, w - 4))[:max(0, w - 4)])
    except curses.error:
        pass

    try:
        stdscr.addstr(top_pad, 0, f"{vmax:4.2f} ┤")
        stdscr.addstr(top_pad + plot_h // 2, 0, f"{(vmin+vmax)/2:4.2f} ┤")
        stdscr.addstr(top_pad + plot_h - 1, 0, f"{vmin:4.2f} ┤")
    except curses.error:
        pass

    for y in (top_pad, top_pad + plot_h // 2, top_pad + plot_h - 1):
        try:
            stdscr.addstr(y, left_pad, "─" * max(0, plot_w))
        except curses.error:
            pass

    if len(values) >= 2 and plot_w > 0 and plot_h > 0:
        data = list(values)[-plot_w:]
        def to_y(v):
            v = max(vmin, min(vmax, v))
            ratio = (v - vmin) / (vmax - vmin) if vmax > vmin else 0
            yy = plot_h - 1 - int(ratio * (plot_h - 1))
            return yy

        prev_y = None
        for i, v in enumerate(data):
            y = to_y(v)
            x = left_pad + i
            if prev_y is not None and x < w:
                y0, y1 = sorted((prev_y, y))
                for yy in range(y0, y1 + 1):
                    try:
                        stdscr.addstr(top_pad + yy, x, "•" if yy == y else "│")
                    except curses.error:
                        pass
            else:
                try:
                    stdscr.addstr(top_pad + y, x, "•")
                except curses.error:
                    pass
            prev_y = y

    last = values[-1] if values else 0.0
    try:
        status = f" last={last:0.3f}V | range {vmin:0.2f}..{vmax:0.2f}V | w={w} h={h}  (Ctrl+C to exit)"
        stdscr.addstr(h - 1, 0, status[:max(0, w - 1)])
    except curses.error:
        pass

    stdscr.noutrefresh()
    curses.doupdate()

def loop(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    values = deque(maxlen=2000)
    vmin, vmax = 0.0, 3.3

    values.append(read_voltage())

    while True:
        try:
            ch = stdscr.getch()
            if ch in (ord('q'), ord('Q')):
                break
        except curses.error:
            pass

        v = read_voltage()
        values.append(v)

        vv = list(values)[-300:]
        lo = min(vv) if vv else 0.0
        hi = max(vv) if vv else 3.3
        margin = max(0.05, (hi - lo) * 0.1)
        vmin = max(0.0, lo - margin)
        vmax = min(3.3, hi + margin) if hi + margin > vmin + 0.1 else vmin + 0.1

        draw_chart(stdscr, values, vmin=vmin, vmax=vmax, title="CH0 Voltage, V")
        time.sleep(0.05)

def destroy():
    adc.close()

def main(stdscr):
    try:
        setup()
        loop(stdscr)
    except KeyboardInterrupt:
        pass
    finally:
        destroy()

if __name__ == "__main__":
    curses.wrapper(main)
