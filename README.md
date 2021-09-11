# TConnect
Toshiba air conditioner interface with ESP32. Uses UART to communicate with AC unit and wifi with other systems. JSON API and web interfaces are provided for the user.

# Hardware
- Espressif ESP32 DevkitC
- Adapter board to connect ESP32 module to AC unit. The hardware is described in this project: https://github.com/toremick/shorai-esp32

# Installation
- Install MicroPython to ESP32 (tested with version 1.16, anything newer should work)
- Copy .py and .html files to ESP32, modify config.py with correct wifi username and password. NOTE: Wifi username and password are saved in plain text to ESP32!

# JSON API
## Status
From address http://yourIP/status following JSON structure is returned:

{"rssi":-58, "state":"OFF", "fanmode":"AUTO", "swing":"OFF", "mode":"FAN", "setpoint":22,  "roomtemp":24,  "outdoortemp":"-"}

- rssi - wifi signal strength
- state - ON, OFF
- fanmode - QUIET, 1, 2, 3, 4, 5, AUTO
- swing - ON, OFF
- mode - AUTO, COOL, HEAT, DRY, FAN
- setpoint - setpoint temperature in C
- roomtemp - room temperature in C
- outdoortemp - outdoor temperature in C, '-' if not available when outdoor unit is not in use

Example of reading status using curl:
>curl http://yourIP/status

## Commands
JSON formatted command can be sent to address http://yourIP/command
- {'CMD_STATE':'STATE_ON'}
- {'CMD_STATE':'STATE_OFF'}
- {'CMD_MODE':'MODE_AUTO'}
- {'CMD_MODE':'MODE_COOL'}
- {'CMD_MODE':'MODE_HEAT'}
- {'CMD_MODE':'MODE_DRY'}
- {'CMD_MODE':'MODE_FAN'}
- {'CMD_FAN':'FANMODE_QUIET'}
- {'CMD_FAN':'FANMODE_1'}
- {'CMD_FAN':'FANMODE_2'}
- {'CMD_FAN':'FANMODE_3'}
- {'CMD_FAN':'FANMODE_4'}
- {'CMD_FAN':'FANMODE_5'}
- {'CMD_FAN':'FANMODE_AUTO'}
- {'CMD_SWING':'SWING_ON'}
- {'CMD_SWING':'SWING_OFF'}
- {'CMD_SETPOINT':setpointvalueinC}

It is perfectly OK to send multiple commands in one message e.g.{'CMD_STATE':'STATE_ON', 'CMD_SWING':'SWING_ON', 'CMD_FAN':'FANMODE_2'}

Example of sending a command using curl: 
>curl -H "Content-Type: application/json" -X POST http://yourIP/command -d "{\"CMD_STATE\":\"STATE_ON\"}"


# Web interface
Opening address http://yourIP/ with a browser shows simple user interface with current status and buttons for commands.

# Links
https://www.espressif.com/en/products/devkits/esp32-devkitc/

https://micropython.org/

https://github.com/toremick/shorai-esp32

https://github.com/belyalov/tinyweb
