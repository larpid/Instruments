"""
device controll class for the LakeShore Temperature Monitor Model 218
so far only used on device with serial: 21EB3L
"""

import fcntl
import serial
from serial.tools import list_ports
import time


class LakeShore218:
    def __init__(self, serial_number='21EB3L'):
        self.serial_number = serial_number
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

            try:
                # lock port to prevent access from multiple scripts
                fcntl.flock(self.ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print('device blocked')
                self.ser.close()
                continue

            try:
                self.ser.write('*IDN?\n'.encode())
                idn_line = self.ser.readline().decode().split(',')
                if len(idn_line) >= 3:
                    if idn_line[2] == self.serial_number:

                        device_found = True
                        print('connection established to LakeShore device %s with S/N: %s' %
                              (comport.device, self.serial_number))
                        break
            except serial.serialutil.SerialException as error_message:
                print(error_message)

            fcntl.flock(self.ser.fileno(), fcntl.LOCK_UN)
            self.ser.close()

        if not device_found:
            self.ser = None
            print('LakeShore device with S/N: %s not found :/' % self.serial_number)
            return

    def disconnect(self):
        self.ser.close()
        self.ser = None
        print('connection closed')

    def read_temp(self, sensor):
        """read temperature of specified sensor (can be 1-8)"""
        self.ser.write(('SRDG? %s\r\n' % sensor).encode())
        return self.ser.readline().decode()

    def log_start(self, continue_last_log=False, interval=20, overwrite_at_full_memory=True, number_of_readings=2):
        """start internal temperature logging

        interval in s
        StorageCapability per Readings: (1500/1, 1000/2, 750/3, 600/4 ...) more details in the Manual
        """

        self.ser.write(('LOGSET 1 %d %d %d %d\r\n' %
                        (overwrite_at_full_memory, continue_last_log, interval, number_of_readings)).encode())

        #time.sleep(1)
        self.ser.write('LOG 1\n'.encode())

    def log_stop(self):
        self.ser.write('LOG 0\n'.encode())
        print([self.ser.readline()])

    def log_read(self, sensors=None):
        if sensors is None:  # avoiding list as default value (mutable)
            sensors = [1, 2]

        # todo: handle readout stop when log full

        data = {'date,time': []}
        for sensor_id in sensors:
            data['sensor%d' % sensor_id] = []

        record_number = 0
        empty_records_reached = False
        while not empty_records_reached:

            date_time = ''

            for sensor_id in sensors:
                self.ser.write(('LOGVIEW? %d %d\r\n' % (record_number, int(sensor_id))).encode())
                record = self.ser.readline().decode().split(',')

                if record[0] == '00/00/00':  # date is zero on unused records
                    empty_records_reached = True
                    print('finished reading log...')
                    break
                if int(record[3]) != 0:
                    print('WARNING: error code %s returned on sensor %s' % (record[3], sensor_id))
                if int(record[4]) != 1:
                    print('WARNING: temperature unit of sensor %s is not Kelvin!' % sensor_id)

                date_time = record[0] + ',' + record[1]
                data['sensor%d' % sensor_id].append(record[2])
            else:
                data['date,time'].append(date_time)
                record_number += 1

        return data

    def log_status(self):
        self.ser.write('LOG?\r\n'.encode())
        return self.ser.readline().decode()
