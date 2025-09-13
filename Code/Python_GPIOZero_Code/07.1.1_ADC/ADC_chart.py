#!/usr/bin/env python3
########################################################################
# Filename    : ADC.py
# Description : Use ADC module to read the voltage value of potentiometer.
# Author      : www.freenove.com
# modification: 2023/05/11
########################################################################
import curses
import time
import random
from ADCDevice import *

adc = ADCDevice() # Define an ADCDevice class object

def setup():
    global adc
    if(adc.detectI2C(0x48)): # Detect the pcf8591.
        adc = PCF8591()
    elif(adc.detectI2C(0x4b)): # Detect the ads7830
        adc = ADS7830()
    else:
        print("No correct I2C address found, \n"
        "Please use command 'i2cdetect -y 1' to check the I2C address! \n"
        "Program Exit. \n");
        exit(-1)

def loop(stdscr):
    height, width = stdscr.getmaxyx()

    while True:
        value = adc.analogRead(0)      # read the ADC value of channel 0
        voltage = value / 255.0 * 3.3  # calculate the voltage value

        # print ('ADC Value : %d, Voltage : %.2f'%(value,voltage))

        y = int((value / 255.0) * (height - 1 - 5))
        x = int((voltage / 3.3) * (width - 1))

        stdscr.clear()
        stdscr.addstr(y, x, "●")
        stdscr.refresh()

        time.sleep(0.1)

def destroy():
    adc.close()
    
def main(stdscr):
    print ('Program is starting ... ')
    try:
        setup()
        loop(stdscr)
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()
        print("Ending program")

curses.wrapper(main)