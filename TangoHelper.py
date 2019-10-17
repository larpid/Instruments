"""
helper classes to use with PyTango
"""

import sys
import serial
from serial.tools import list_ports
import fcntl


class StoreStdOut(object):
    """Helper Class to store last stdout message"""
    # todo: try to change to only overwrite stuff so sys.stdout.flush() keeps being usable

    def __init__(self):
        self.stdout_orig = sys.stdout
        self.last_message = ''

    def write(self, message):
        self.stdout_orig.write(message)
        if message != '\n':
            self.last_message = message

    def read_stored_message(self):
        return self.last_message

    # functions inherited from sys.stdout object (there might be a cleaner way to do this automatically)
    def flush(self, *args, **kwargs):
        self.stdout_orig.flush(*args, **kwargs)


def connect_by_serial_number(serial_connection, serial_number, idn_message='*IDN?\n', idn_answer_check_function=None):
    """handle connection by serial number instead of a fixed port
    returns: bool(connection successful?)

    takes a serial.Serial() object as serial_connection and a serial number (S/N) of the device
    acquirable by *IDN? call to find the right port"""

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
            serial_connection.write(idn_message.encode())
            idn_line = serial_connection.readline()
            if idn_answer_check_function is None:
                idn_line = idn_line.decode().split(',')
                if len(idn_line) >= 3:
                    if idn_line[2] == serial_number:
                        print('connection established to device %s with S/N: %s' %
                              (comport.device, serial_number))
                        return True
            else:
                if idn_answer_check_function(idn_line, serial_number):
                    print('connection established to device %s with S/N: %s' %
                          (comport.device, serial_number))
                    return True

        except serial.serialutil.SerialException as error_message:
            print(error_message)

        fcntl.flock(serial_connection.fileno(), fcntl.LOCK_UN)
        serial_connection.close()

    else:
        print('Device with S/N: %s not found :/' % serial_number)
        return False
