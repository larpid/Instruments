"""
device control class for the VACOM MVC3 vacuum gauge controller
so far only used on devices with serial: todo:add these
"""

import serial
import TangoHelper


class MVC3GaugeController:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.ser = serial.Serial()

    def connect(self):
        if self.ser.is_open:
            print('device already connected')
            return True

        self.ser = serial.Serial(baudrate=19200,
                                 timeout=1,
                                 bytesize=8,
                                 parity=serial.PARITY_NONE,
                                 stopbits=1)

        if not TangoHelper.connect_by_serial_number(self.ser, self.serial_number, idn_message='*IDN?\r'):
            return False

        print('connection established')
        return True

    def disconnect(self):
        self.ser.close()
        print('connection closed')

    def read_pressure(self, channel):
        """read pressure of specified channel (can be 1,2 or 3)"""
        self.ser.write(('RPV? %s\n' % channel).encode())
        return float(self.ser.readline().decode().strip())


if __name__ == "__main__":
    """test code"""
    gc1 = MVC3GaugeController(0)
    gc1.connect()
