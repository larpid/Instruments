import serial
from serial.tools import list_ports
from pathlib import Path


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
i = 1
ser.write(('LOGVIEW? %d 1\n' % i).encode())
sens1 = ser.readlines()[0].decode().split(',')


file = open('/media/chamber7/Data/TempMessur/lakeShore'+sens1[0].replace('/','')+'-' + sens1[1].replace(':','') + 'Uhr' + '.txt', 'w+')
file.write('date\ttime\ttempSiDiode(K)\ttempPt100(K)\n')

while i != 0:

    ser.write(('LOGVIEW? %d 1\n' % i).encode())
    sens1 = ser.readlines()[0].decode().split(',')



    ser.write(('LOGVIEW? %d 2\n' % i).encode())
    sens2 = ser.readlines()[0].decode().split(',')


    if sens1[0] != '00/00/00':
        print('%d ' % i, end='')
        file.write(sens1[0] + '\t' + sens1[1] + '\t' + sens1[2] + '\t')
        file.write(sens2[2] + '\n')


        if i == 1:
            j = sens1[1].split(':')
            k = sens1[0]

        i = i + 1
        l=sens1[0]
    else:
        m = sens1[1].split(':')
        file.write('Messung vom' + '\t' + k + '\t' + 'Messdauer:' + '\t' + str((i-2)*30)+ 's' + '\t' + '\t' + 'Messpunkte:'+ '\t' + str(i-1) + '\t' )
        i = 0



print('file finished')
