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

        print('INFO: Connection call uses Serial Address instead of S/N on this device')

        self.ser = serial.Serial(baudrate=19200,
                                 timeout=1,
                                 bytesize=8,
                                 parity=serial.PARITY_NONE,
                                 stopbits=1)

        def idn_answer_check_function(idn_line, serial_address):
            if len(idn_line) > 0:
                try:
                    if int(idn_line.strip(), 16) == serial_address:  # data is 1 byte
                        return True
                except ValueError as error:
                    print(error)
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
        if self.ser.is_open:
            self.ser.close()
            print('connection closed')

    def read_pressure(self, channel, decimal_places=2):
        """read pressure of specified channel (can be 1,2 or 3)"""

        status_messages = {0: "",  # Measuring Value OK
                           1: " (Measuring Value < Measuring Range)",
                           2: " (Measuring Value > Measuring Range)",
                           3: " Err Lo",  # Measuring range undershooting
                           4: " Err Hi",  # Measuring range overshooting
                           5: " oFF",  # Sensor off
                           6: " HV on",  # HV on (displays HU on on device probably due to 7 segment display limitation)
                           7: " Err S",  # Sensor Error
                           8: " Err bA",  # BA error
                           9: " no Sen",  # No Sensor
                           10: " notriG",  # No switch on or switch off point
                           11: " Err P",  # Pressure value overstepping
                           12: " Err Pi",  # Pirani error ATMION
                           13: " Err 24",  # Breakdown of operational voltage
                           14: " FiLbr"}  # Filament defectively

        self.ser.write(('RPV%s\r' % channel).encode())
        answer = self.ser.readline().decode().strip().split('\t')
        if answer[0] == '?':
            if answer[1] == 'S,':
                # no sensor on this channel connected
                return 'no sensor'
            else:
                return 'ERROR: device reports error info %s' % answer
        return "{:.{}f}".format(float(answer[1]), decimal_places) + status_messages[int(answer[0].strip(','))]


if __name__ == "__main__":
    """test code"""
    gc1 = MVC3GaugeController(70)
    gc1.connect()
    print(gc1.read_pressure(2))
    gc1.disconnect()
