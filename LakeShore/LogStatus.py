import serial
from serial.tools import list_ports

ser = serial.Serial(port='/dev/ttyUSB4',
                    baudrate=9600,
                    timeout=1,
                    bytesize=7,
                    parity='O',
                    stopbits=1)


ser.write('*IDN?\n'.encode())
print(ser.readlines())

ser.write('LOG?\n'.encode())
sens1 = ser.readlines()[0].decode()
if int(sens1) == 1:
    print('Log ON')
else:
    print('Log OFF')