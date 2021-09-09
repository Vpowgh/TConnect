'''
boot.py
TConnect - ESP32 based interface for Toshiba air conditioners
Developed by Vpow 2021-
'''

import machine
import network
import time
import config
import logging
logging.basicConfig(level=logging.DEBUG)

logging.info("TConnect")
logging.info("Toshiba Air Conditioner control via UART")

#if not power reset or hard reset, make hard reset
if(machine.reset_cause() > 2):
    machine.reset()

#init UART
uart = machine.UART(1, 9600)
uart.init(9600, bits=8, parity=0, stop=1, rx=32, tx=33, timeout=10, timeout_char=50)

# Connect to WiFi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

if not sta_if.isconnected():
    logging.info("Connecting to network")
    sta_if.connect(config.WIFISSID, config.WIFIPWD)
    
    while not sta_if.isconnected():
        time.sleep(0.5)

logging.info("Connected:" + str(sta_if.ifconfig()))