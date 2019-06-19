import serial
from serial.tools import list_ports
import time

SERIAL_NUMBER = '21EB3L'


class LakeShore:
    def __init__(self):
        self.ser = None

    def connect(self):
        if self.ser is not None:
            print('device already connected')
            return

        # # connection handling
        device_found = False

        # try connections to find right serial number
        for comport in list_ports.comports():
            self.ser = serial.Serial(port=comport.device,
                                     baudrate=9600,
                                     timeout=1,
                                     bytesize=7,
                                     parity='O',
                                     stopbits=1)
            print('test connection established to device: ' + comport.device)

            self.ser.write('*IDN?\n'.encode())
            idn_line = self.ser.readline().decode().split(',')
            if len(idn_line) >= 3:
                if idn_line[2] == SERIAL_NUMBER:

                    device_found = True
                    print('connection established to LakeShore device with S/N: ' + SERIAL_NUMBER)
                    break

            self.ser.close()

        if not device_found:
            self.ser = None
            print('LakeShore device with S/N: %s not found :/' % SERIAL_NUMBER)
            return

    def disconnect(self):
        self.ser.close()
        self.ser = None
        print('connection closed')

    def read_temp(self, sensor):
        """read temperature of specified sensor (can be 1-8)"""
        self.ser.write(('SRGD? %d\r\n' % sensor).encode())
        return self.ser.readline().decode()

    def log_start(self, continue_last_log=False, interval=20, overwrite_at_full_memory=True, number_of_readings=2):
        """start internal temperature logging

        interval in s
        StorageCapability per Readings: (1500/1, 1000/2, 750/3, 600/4 ...) more details in the Manual
        """

        self.ser.write(('LOGSET 1 %d %d %d %d\r\n' %
                        (overwrite_at_full_memory, continue_last_log, interval, number_of_readings)).encode())

        time.sleep(.3)
        self.ser.write('LOG 1\r\n'.encode())

    def log_stop(self):
        self.ser.write('LOG 0\r\n'.encode())

    def log_read(self, sensors=None):
        if sensors is None:
            sensors = [1, 2]

        empty_records_reached = False
        record_number = 0

        while not empty_records_reached:
            record = []
            for sensor_id in sensors:
                self.ser.write(('LOGVIEW? %d %d\r\n' % (record_number, sensor_id)).encode())
                record.append(self.ser.readline().decode().split(','))


        self.ser.write(('LOGVIEW? %d 2\r\n' % i).encode())
        sens2 = ser.readlines()[0].decode().split(',')

        pass

    def log_status(self):
        self.ser.write('LOG?\r\n'.encode())
        return self.ser.readline().decode()
