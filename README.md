# TConnect
Toshiba air conditioner control via UART

## JSON API
### Status
Connect to yourIP/status and following JSON structure is returned:

{"rssi":-58, "state":"OFF", "fanmode":"AUTO", "swing":"OFF", "mode":"FAN", "setpoint":22,  "roomtemp":24,  "outdoortemp":"-"}


commands = {'CMD_STATE':128, 'CMD_MODE':176, 'CMD_FAN':160, 'CMD_SWING':163, 'CMD_SETPOINT':179,
            'MODE_AUTO':65, 'MODE_COOL':66, 'MODE_HEAT':67, 'MODE_DRY':68, 'MODE_FAN':69,
            'FANMODE_QUIET':49, 'FANMODE_1':50, 'FANMODE_2':51, 'FANMODE_3':52, 'FANMODE_4':53, 'FANMODE_5':54, 'FANMODE_AUTO':65,
            'SWING_OFF': 49, 'SWING_ON':65, 'STATE_ON':48, 'STATE_OFF':49}
