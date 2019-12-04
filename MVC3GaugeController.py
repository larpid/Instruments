"""
device control class for the VACOM MVC3 vacuum gauge controller
"""

import serial
import TangoHelper


class MVC3GaugeController:
    def __init__(self, serial_address):
        self.serial_address = serial_address
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

        def idn_answer_check_function(idn_line, serial_address):
            if len(idn_line) > 0:
                print('Connection call uses Serial Address instead of S/N on this device')
                if int(idn_line.strip(), 16) == serial_address:  # data is 1 byte
                    return True
            return False

        # connection on this device is not done by asking for the serial number (not supported by device) but by
        # asking for the RS485 Serial Address (can also be set/requested in the here used RS232 mode). These were
        # manually set with SSA (e.g. 'RSA46\r' sets this to hex value 46 which is 70 in decimal) command and are
        # labeled on the case of each device. IMPORTANT: after setting the serial address the device must be switched
        # to RS485 and can then be switched back to RS232 immediately. Otherwise the address will reset on next device
        # restart
        if not TangoHelper.connect_by_serial_number(self.ser, serial_number=self.serial_address, idn_message='RSA\r',
                                                    idn_answer_check_function=idn_answer_check_function):
            return False

        print('connection established')
        return True

    def disconnect(self):
        self.ser.close()
        print('connection closed')

    def read_pressure(self, channel):
        """read pressure of specified channel (can be 1,2 or 3)"""
        self.ser.write(('RPV%s\r' % channel).encode())
        answer = self.ser.readline().decode().strip().split('\t')
        if answer[0] == '?':
            if answer[1] == 'S,':
                # no sensor on this channel connected
                return None
            else:
                print('ERROR: device reports error info %s' % answer)
                return None
        return float(answer[1])


if __name__ == "__main__":
    """test code"""
    gc1 = MVC3GaugeController(70)
    gc1.connect()
    print(gc1.read_pressure(2))
    gc1.disconnect()
