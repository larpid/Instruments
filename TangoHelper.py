"""
helper classes to use with PyTango
"""

import sys
import serial
from serial.tools import list_ports
import fcntl


class StoreStdOut(object):
    """Helper Class to store last stdout message"""

    def __init__(self):
        self.terminal = sys.stdout
        self.last_message = ''

    def write(self, message):
        self.terminal.write(message)
        if message != '\n':
            self.last_message = message

    def read(self):
        return self.last_message

def portfinder(serial_connection, serial_number):
    """takes a serial.Serial() object as serial_connection and a serial number (S/N) of the device
    aquireable by *IDN? call to find the right port"""

    # # connection handling
    device_found = False

    # try connections to find right serial number
    for comport in list_ports.comports():
        serial_connection.port = comport.device
        serial_connection.open()
        print('test connection established to device: %s' % comport.device)

        try:
            # lock port to prevent access from multiple scripts
            fcntl.flock(serial_connection.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('device blocked')
            serial_connection.close()
            continue

        try:
            serial_connection.write('*IDN?\n'.encode())
            idn_line = serial_connection.readline().decode().split(',')
            if len(idn_line) >= 3:
                if idn_line[2] == serial_number:
                    device_found = True
                    print('connection established to device %s with S/N: %s' %
                          (comport.device, serial_number))
                    break
        except serial.serialutil.SerialException as error_message:
            print(error_message)

        fcntl.flock(serial_connection.fileno(), fcntl.LOCK_UN)
        serial_connection.close()

    if not device_found:
        serial_connection = None
        print('Device with S/N: %s not found :/' % serial_number)
        return
