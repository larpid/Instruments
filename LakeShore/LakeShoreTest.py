import serial
from serial.tools import list_ports


#for eachport in list_ports.comports():
#    print([eachport.device, eachport.manufacturer, eachport.description, eachport.product])

ser = serial.Serial(port='/dev/ttyUSB4',
                    baudrate=9600,
                    timeout=1,
                    bytesize=7,
                    parity='O',
                    stopbits=1)


ser.write('*IDN?\n'.encode())

print(ser.readlines())

file = open('/media/chamber7/Data/TEMP_TDC_test/lakeShore.txt', 'w')
file.write('date\ttime\ttempSiDiode(K)\ttempPt100(K)\n')

for i in range(1, 10):
    print('%d ' % i, end='')
    ser.write(('LOGVIEW? %d 1\r\n' % i).encode())
    sens1 = ser.readlines()[0].decode().split(',')

    print(sens1[0]+ '\t' +sens1[1] +'\t'+sens1[2]+'\t',end= '')

    ser.write(('LOGVIEW? %d 2\r\n' % i).encode())
    sens2 = ser.readlines()[0].decode().split(',')
    print(sens2[2] + '\n')

print('file finished')


