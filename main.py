'''
main.py
TConnect - ESP32 based interface for Toshiba air conditioners
Developed by Vpow 2021-
'''

import tinyweb
import machine
import gc
import logging
logging.basicConfig(level=logging.DEBUG)


import uasyncio as asyncio

#--------------------------------------------------------------
#Web server

#handle incoming POST request
class JSONCommands():
    def post(self, data):
        logging.info(str(data))
        for i in data:
            sendcommand(i,data[i])
        return 'OK', 200
    
# Create web server application
app = tinyweb.webserver()
app.add_resource(JSONCommands, '/command')

# Index page
@app.route('/')
@app.route('/index.html')
async def index(request, response):
    await response.send_file('./webUI.html')

@app.route('/status')
async def index(request, response):
    await response.send('HTTP/1.0 200 OK\r\n')
    await response.send('Content-Type: application/json; charset=utf-8\r\n')
    await response.send('\r\n')    
    await response.send('{' +
    '"rssi":' + str(getrssi()) +
    ', "state":"' + str(UIstate[values[VAL_STATE]]) +
    '", "fanmode":"' + str(UIfanmode[values[VAL_FANMODE]]) +
    '", "swing":"' + str(UIswing[values[VAL_SWING]]) +
    '", "mode":"' + str(UImode[values[VAL_MODE]]) +
    '", "smode":"' + str(UImode[values[VAL_SMODE]]) +
    '", "ontimer":"' + str(UImode[values[VAL_ONTIMER]]) +
    '", "offtimer":"' + str(UImode[values[VAL_OFFTIMER]]) +
    '", "setpoint":' + str(values[VAL_SETPOINT]) +
    ',  "roomtemp":' + str(convert_temperature(values[VAL_ROOMTEMP])) +
    ',  "outdoortemp":"' + str(convert_temperature(values[VAL_OUTDOORTEMP])) +
    '"}\n')

async def all_shutdown():
    await asyncio.sleep_ms(100)


#--------------------------------------------------------------
#Wifi
rssi = 0

def getrssi():
    return rssi

#--------------------------------------------------------------
#UART serial communication
COMM_INIT = const(1)
COMM_NORMAL = const(2)

commands = {'CMD_STATE':128, 'CMD_ONTIMER':144, 'CMD_ONTIMERVALUE':146, 'CMD_OFFTIMER':148, 'CMD_OFFTIMERVALUE':150, 'CMD_MODE':176, 'CMD_FAN':160, 'CMD_SWING':163, 'CMD_SETPOINT':179, 'CMD_SMODE':247,
            'MODE_AUTO':65, 'MODE_COOL':66, 'MODE_HEAT':67, 'MODE_DRY':68, 'MODE_FAN':69,
            'FANMODE_QUIET':49, 'FANMODE_1':50, 'FANMODE_2':51, 'FANMODE_3':52, 'FANMODE_4':53, 'FANMODE_5':54, 'FANMODE_AUTO':65,
            'SWING_OFF':49, 'SWING_ON':65, 'STATE_ON':48, 'STATE_OFF':49,
            'SMODE_OFF':0, 'SMODE_HIPOWER':1, 'SMODE_ECOCOMFORTSLEEP':3, 'SMODE_8C':4, 'SMODE_FP1':32, 'SMODE_FP2':48,
            'ONTIMER_ON':65, 'ONTIMER_OFF':66, 'OFFTIMER_ON':65, 'OFFTIMER_OFF':66}
UImode =    {0:'-', 65:'AUTO', 66:'COOL', 67:'HEAT', 68:'DRY', 69:'FAN'}
UISmode =   {0:'OFF', 1:'HIPOWER', 3:'ECO/COMFORT', 4:'8C', 32:'FAN', 48:'FAN'}
UIfanmode = {0:'-', 49:'QUIET', 50:'1', 51:'2', 52:'3', 53:'4', 54:'5', 65:'AUTO'}
UIswing =   {0:'-', 49:'OFF', 65:'ON'}
UIstate =   {0:'-', 48:'ON', 49:'OFF'}
UIontimer = {0:'-', 65:'ON', 66:'OFF'}
UIofftimer ={0:'-', 65:'ON', 66:'OFF'}


values = {128:0, 144:0, 146:0, 148:0, 150:0, 160:0, 163:0, 176:0, 179:0, 187:0, 190:0, 247:0}
VAL_STATE = const(128)
VAL_ONTIMER = const(144)
VAL_ONTIMERVALUE = const(146)
VAL_OFFTIMER = const(148)
VAL_OFFTIMERVALUE = const(150)
VAL_FANMODE = const(160)
VAL_SWING = const(163)
VAL_MODE = const(176)
VAL_SETPOINT = const(179)
VAL_ROOMTEMP = const(187)
VAL_OUTDOORTEMP = const(190)
VAL_SMODE = const(247)

comm_state = COMM_INIT
comm_errorcounter = 0

rxdata = b'' #buffer for incoming bytes
rxwait = False

txmsg = [] # buffer for outgoing messages


def checksum(s):
    return (0x100-(sum(s)%0x100))%0x100

def init_comms():
    global txmsg
        
    logging.info("Comm init")
    
    txmsg.append(((2,255,255,0,0,0,0,2),100))
    txmsg.append(((2,255,255,1,0,0,1,2,254),100))
    txmsg.append(((2,0,0,0,0,0,2,2,2,250),100))
    txmsg.append(((2,0,1,129,1,0,2,0,0,123),100))
    txmsg.append(((2,0,1,2,0,0,2,0,0,254),100))
    txmsg.append(((2,0,2,0,0,0,0,254),2000))
    txmsg.append(((2,0,2,1,0,0,2,0,0,251),100))
    txmsg.append(((2,0,2,2,0,0,2,0,0,250),100))

def convert_temperature(t):
    if(t>127):
        return (t-256)
    elif(t==127):
        return '-'
    else:
        return t


def getvalue(v):
    global txmsg
    msg = [2,0,3,16,0,0,6,1,48,1,0,1]
    msg.append(v)
    msg.append(checksum(msg[1:]))    
    txmsg.append((msg,100))

def sendcommand(c,v):
    global txmsg
    msg = [2,0,3,16,0,0,7,1,48,1,0,2]
    logging.debug("CMD: %s %s",str(c),str(v))

    if(c=='CMD_SETPOINT' and int(v)>0 and int(v)<50):
        msg.append(commands[c])
        msg.append(int(v))
    elif(c in commands and v in commands):
        msg.append(commands[c])
        msg.append(commands[v])
    else:
        return #command not valid, do not send anything
    
    msg.append(checksum(msg[1:]))
    txmsg.insert(0,(msg,100))

def parsemessage(m):
    if(m[2] == 0x03 and len(m) == 17): #read response
        code = m[14]
        value = m[15]
        if(code in values):
            values[code] = value
            logging.debug("%s",str(values))

def comm_error():
    return (comm_errorcounter>=5)

async def UART_transmitter():
    global txmsg
    global rxwait
    
    delay = 50
    
    while True:
        while(len(txmsg) > 0):
            x = txmsg.pop(0)
            logging.debug("S: %s",bytearray(x[0]))
            uart.write(bytearray(x[0]))
            delay=x[1]
            if(delay < 50):
               delay = 50
            elif(delay > 5000):
               delay = 5000
            await asyncio.sleep_ms(delay)
            rxwait = True
            
        await asyncio.sleep_ms(50)

async def UART_receiver():
    global rxdata
    global rxwait
    global comm_errorcounter
    
    while True:
        if(uart.any() > 0): #new data received
            rxdata = rxdata + uart.read()
        elif(rxwait): #nothing received but waited
            rxwait = False
            logging.info("TIMEOUT")
            newstart = rxdata.find(b'\x02',1) #it is possible that msglen was garbage and there is still valid message in the buffer, find it
            if(newstart >= 0):
                rxdata = rxdata[newstart:]
                logging.debug("TO: %s %s",str(newstart),str(rxdata))
            else:
                rxdata = b''
                logging.info("FLUSH3")
                if(comm_errorcounter < 5):
                    comm_errorcounter = comm_errorcounter + 1
                    logging.info("CER")
        
        bufferlen = len(rxdata)
        
        while(bufferlen > 7):
            logging.debug("bufferlen: %s",str(bufferlen))
            if(rxdata[0] == 0x02): #check correct start byte
                msglen = rxdata[6]
                logging.debug("msglen: %s",str(msglen))
                if(bufferlen > 7+msglen): #check if whole message in buffer
        
                    if(checksum(rxdata[1:7+msglen]) == rxdata[7+msglen]):
                        logging.info("MSGOK")
                        logging.debug("%s",str(rxdata[:(8+msglen)]))
                        parsemessage(rxdata[:(8+msglen)])
                        rxdata = rxdata[(8+msglen):] #remove message from buffer
                        comm_errorcounter = 0
                    else: #wrong checksum
                        logging.info("CSERR")
                        newstart = rxdata.find(b'\x02',1)
                        if(newstart >= 0):
                            rxdata = rxdata[newstart:]
                        else:
                            rxdata = b''
                            logging.info("FLUSH1")
                            
                else: #wait more bytes
                    logging.info("WAIT")
                    rxwait = True
                    break
            else:
                newstart = rxdata.find(b'\x02',1)
                if(newstart >= 0):
                    rxdata = rxdata[newstart:]
                else:
                    rxdata = b''
                    logging.info("FLUSH2")

            bufferlen = len(rxdata)
            
        await asyncio.sleep_ms(1000)

#--------------------------------------------------------------

async def mainloop():
    global comm_state
    global rssi
    
    while True:
        logging.info("4s")
        
        if sta_if.isconnected(): #rssi can be read only if wifi connected
            if(rssi == 0):
                rssi = sta_if.status('rssi')
            else:
                rssi = int(rssi + (sta_if.status('rssi')-rssi)/4) #filtered rssi value
        
        if(comm_state == COMM_NORMAL):
            if not comm_error():
                for k in values:
                    getvalue(k)
            else:
                comm_state = COMM_INIT
        elif(comm_state == COMM_INIT):
            init_comms()
            comm_state = COMM_NORMAL
        else: #should not end up here
            comm_state = COMM_INIT

        gc.collect()
        await asyncio.sleep_ms(4000)

#--------------------------------------------------------------



#------------------------------------------------------------------------        
#add coroutines and run
app.loop.create_task(UART_receiver())
app.loop.create_task(UART_transmitter())
app.loop.create_task(mainloop())

try:
    app.run(host='0.0.0.0', port=80)
except KeyboardInterrupt as e:
    logging.info(' CTRL+C pressed - terminating...')
    app.shutdown()
    uasyncio.get_event_loop().run_until_complete(all_shutdown())
#------------------------------------------------------------------------        
