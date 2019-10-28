import serial
from serial.tools import list_ports
import time



# for eachport in list_ports.comports():
#    print([eachport.device, eachport.manufacturer, eachport.description, eachport.product])

ser = serial.Serial(port='/dev/ttyUSB4',
                    baudrate=9600,
                    timeout=1,
                    bytesize=7,
                    parity='O',
                    stopbits=1)

ser.write('*IDN?\n'.encode())
print(ser.readlines())

# ON/OFF
#x = 1 #ON
x = 0  #OFF

# Log reading

# StorigeCapability per Readings: (1500/1, 1000/2, 750/3, 600/4 ...) more details in the Manual

# Intervall in s
p = 30

# Logging continues/stops (old Records will be destroyed when memory is full/Log stops with full memory)
#o = 1      #continues
o = 0  #stops

# Clear/Continue  (Stop/Start deletes all logged data/or continues logging in same memory "your Dataprint has all Data mixed")
s = 0  # clears(deletes old data)
#s = 1    #continue

# logged Value
# v =
# K = , C = ,SensorUnit = , LinearEquation=

# number of readings
r = 2

ser.write(('LOGSET 1 %d %d %d %d\n' % (o, s, p, r)).encode())

time.sleep(0.1)
ser.write(('LOG ' + str(x) + '\n').encode())
time.sleep(0.1)
ser.write('LOG?\n'.encode())
sens1 = ser.readlines()[0].decode()
time.sleep(0.1)
if int(sens1) == 1:
    print('Log ON')
else:
    print('Log OFF')

ser.write('LOGSET?\n'.encode())
sens1 = ser.readlines()[0].decode()
print(sens1)





#temp1
#temp2
#logstart
#logstop
#logcontinue
#logread
