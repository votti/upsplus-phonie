#!/usr/bin/env python3

# '''Enable Auto-Shutdown Protection Function '''

import os
import time
import smbus2
import logging
from ina219 import INA219,DeviceRangeError
from subprocess import call

class UnblockPins:
    ON_STATE='a0'
    OFF_STATE='ip'
    def __init__(self, pins: list[str]):
        self.pins = pins

    def __enter__(self):
        for pin in self.pins:
            call(['raspi-gpio', 'set', str(pin), self.ON_STATE])
    def __exit__(self, type, value, traceback):
        for pin in self.pins:
            call(['raspi-gpio', 'set', str(pin), self.OFF_STATE])


# Define I2C bus
DEVICE_BUS = 1

# Define device i2c slave address.
DEVICE_ADDR = 0x17

# Set the threshold of UPS automatic power-off to prevent damage caused by battery over-discharge, unit: mV.
PROTECT_VOLT = 3700  

# Set the sample period, Unit: min default: 2 min.
SAMPLE_TIME = 2

# Enable Back-to-AC fucntion.
# Enable: write 1 to register 0x19 == 25
# Disable: write 0 to register 0x19 == 25
BACK_TO_AC = 0

def check_battery():
    # Instance INA219 and getting information from it.
    ina_supply = INA219(0.00725, busnum=DEVICE_BUS, address=0x40)
    with UnblockPins([2,3]) as up:
        ina_supply.configure()
        supply_voltage = ina_supply.voltage()
        supply_current = ina_supply.current()
        supply_power = ina_supply.power()
    print("-"*60)
    print("------Current information of the detected Raspberry Pi------")
    print("-"*60)
    print("Raspberry Pi Supply Voltage: %.3f V" % supply_voltage)
    print("Raspberry Pi Current Current Consumption: %.3f mA" % supply_current)
    print("Raspberry Pi Current Power Consumption: %.3f mW" % supply_power)
    print("-"*60)

    # Batteries information
    ina_batt = INA219(0.005, busnum=DEVICE_BUS, address=0x45)
    with UnblockPins([2,3]) as up:
        ina_batt.configure()
        batt_voltage = ina_batt.voltage()
        batt_current = ina_batt.current()
        batt_power = ina_batt.power()
    print("-------------------Batteries information-------------------")
    print("-"*60)
    print("Voltage of Batteries: %.3f V" % batt_voltage)
    try:
        if batt_current > 0:
            print("Battery Current (Charging) Rate: %.3f mA"% batt_current)
            print("Current Battery Power Supplement: %.3f mW"% batt_power)
        else:
            print("Battery Current (discharge) Rate: %.3f mA"% batt_current)
            print("Current Battery Power Consumption: %.3f mW"% batt_power)
            print("-"*60)
    except DeviceRangeError:
         print("-"*60)
         print('Battery power is too high.')

    # Raspberry Pi Communicates with MCU via i2c protocol.
    bus = smbus2.SMBus(DEVICE_BUS)

    aReceiveBuf = []
    aReceiveBuf.append(0x00) 

    # Read register and add the data to the list: aReceiveBuf
    with UnblockPins([2,3]) as up:
        for i in range(1, 255):
            aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))

    # Enable Back-to-AC fucntion.
    # Enable: write 1 to register 0x19 == 25
    # Disable: write 0 to register 0x19 == 25

    with UnblockPins([2,3]) as up:
        bus.write_byte_data(DEVICE_ADDR, 25, BACK_TO_AC)

        # Reset Protect voltage
        bus.write_byte_data(DEVICE_ADDR, 17, PROTECT_VOLT & 0xFF)
        bus.write_byte_data(DEVICE_ADDR, 18, (PROTECT_VOLT >> 8)& 0xFF)
    print("Successfully set the protection voltage to: %d mV" % PROTECT_VOLT)

    if (aReceiveBuf[8] << 8 | aReceiveBuf[7]) > 4000:
        print('-'*60)
        print('Currently charging via Type C Port.')
    elif (aReceiveBuf[10] << 8 | aReceiveBuf[9])> 4000:
        print('-'*60)
        print('Currently charging via Micro USB Port.')
    else:
        print('-'*60)
        print('Currently not charging.')
        # Consider shutting down to save data or send notifications
        if ((batt_voltage * 1000) < (PROTECT_VOLT + 200)):
            print('-'*60)
            print('The battery is going to dead! Ready to shut down!')
            # It will cut off power when initialized shutdown sequence.
            with UnblockPins([2,3]) as up:
                bus.write_byte_data(DEVICE_ADDR, 24,240)
            if TESTMODE == False:
                os.system("sudo sync && sudo halt")
                while True:
                    time.sleep(10)
            else:
                print("Would initiate shutdown")

if __name__ == '__main__':

    TESTMODE = False
    CHECK_INTERVAL = 120
    check_done = False
    while check_done == False:
        try:
            check_battery()
            check_done = True
        except OSError as error:
            print(error)
