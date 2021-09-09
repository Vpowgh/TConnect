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
COMM_INIT = 1
COMM_NORMAL = 2

commands = {'CMD_STATE':128, 'CMD_MODE':176, 'CMD_FAN':160, 'CMD_SWING':163, 'CMD_SETPOINT':179,
            'MODE_AUTO':65, 'MODE_COOL':66, 'MODE_HEAT':67, 'MODE_DRY':68, 'MODE_FAN':69,
            'FANMODE_QUIET':49, 'FANMODE_1':50, 'FANMODE_2':51, 'FANMODE_3':52, 'FANMODE_4':53, 'FANMODE_5':54, 'FANMODE_AUTO':65,
            'SWING_OFF': 49, 'SWING_ON':65, 'STATE_ON':48, 'STATE_OFF':49}
UImode =    {0:'-', 65:'AUTO', 66:'COOL', 67:'HEAT', 68:'DRY', 69:'FAN'}
UIfanmode = {0:'-', 49:'QUIET', 50:'1', 51:'2', 52:'3', 53:'4', 54:'5', 65:'AUTO'}
UIswing =   {0:'-', 49:'OFF', 65:'ON',}
UIstate =   {0:'-', 48:'ON', 49:'OFF'}


values = {128:0, 160:0, 163:0, 176:0, 179:0, 187:0, 190:0}
VAL_STATE = 128
VAL_FANMODE = 160
VAL_SWING = 163
VAL_MODE = 176
VAL_SETPOINT = 179
VAL_ROOMTEMP = 187
VAL_OUTDOORTEMP = 190

comm_state = COMM_INIT
comm_errorcounter = 0

rxdata = b'' #buffer for incoming bytes
rxwait = False


def checksum(s):
    return (0x100-(sum(s)%0x100))%0x100

def init_comms():
    global comm_errorcounter
        
    logging.info("Comm init")
    
    comm_errorcounter = 0
    
    msglist = []
    msglist.append((2,255,255,0,0,0,0,2))
    msglist.append((2,255,255,1,0,0,1,2,254))
    msglist.append((2,0,0,0,0,0,2,2,2,250))
    msglist.append((2,0,1,129,1,0,2,0,0,123))
    msglist.append((2,0,1,2,0,0,2,0,0,254))
    msglist.append((2,0,2,0,0,0,0,254))
    
    for i in msglist:
        logging.debug("%s",bytearray(i))
        uart.write(bytearray(i))
        time.sleep(0.1)
     
    time.sleep(2)
    msglist.clear()
    msglist.append((2,0,2,1,0,0,2,0,0,251))
    msglist.append((2,0,2,2,0,0,2,0,0,250))

    for i in msglist:
        logging.debug("%s",bytearray(i))
        uart.write(bytearray(i))
        time.sleep(0.1)


def convert_temperature(t):
    if(t>127):
        return (t-256)
    elif(t==127):
        return '-'
    else:
        return t


def getvalue(v):
    msg = [2,0,3,16,0,0,6,1,48,1,0,1]
    msg.append(v)
    msg.append(checksum(msg[1:]))    
    logging.debug("%s",bytearray(msg))
    uart.write(bytearray(msg))
    time.sleep(0.1) #have to give some time to AC


def sendcommand(c,v):
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
    logging.debug("%s",bytearray(msg))
    uart.write(bytearray(msg))
    time.sleep(0.05) #have to give some time to AC


def parsemessage(m):
    if(m[2] == 0x03 and len(m) == 17): #read response
        code = m[14]
        value = m[15]
        if(code in values):
            values[code] = value
            logging.debug("%s",str(values))

def comm_error():
    global comm_errorcounter
    return (comm_errorcounter>=5)

def UART_receiver():
    global rxdata
    global rxwait
    global comm_errorcounter
    
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
            return
    else: #nothing received
        if(comm_errorcounter < 5):
            comm_errorcounter = comm_errorcounter + 1
        return
    
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

#--------------------------------------------------------------

def loop_4s(timer):
    global comm_state
    global rssi
    
    logging.info("4s")
    
    if(rssi == 0):
        rssi = sta_if.status('rssi')
    else:
        rssi = int(rssi + (sta_if.status('rssi')-rssi)/4) #filtered rssi value
    
    UART_receiver()
    
    if(comm_state == COMM_NORMAL):
        if not comm_error():
            getvalue(VAL_STATE)
            getvalue(VAL_FANMODE)
            getvalue(VAL_SWING)
            getvalue(VAL_MODE)
            getvalue(VAL_SETPOINT)
            getvalue(VAL_ROOMTEMP)
            getvalue(VAL_OUTDOORTEMP)
        else:
            comm_state = COMM_INIT
    elif(comm_state == COMM_INIT):
        init_comms()
        comm_state = COMM_NORMAL
    else: #should not end up here
        comm_state = COMM_INIT

    gc.collect()
#--------------------------------------------------------------



#------------------------------------------------------------------------        
#run main application
timer = machine.Timer(0)
timer.init(period=4000, mode=machine.Timer.PERIODIC, callback=loop_4s)

#run web server
try:
    app.run(host='0.0.0.0', port=80)
except KeyboardInterrupt as e:
    logging.info(' CTRL+C pressed - terminating...')
    timer.deinit()
    app.shutdown()
    uasyncio.get_event_loop().run_until_complete(all_shutdown())
#------------------------------------------------------------------------        
