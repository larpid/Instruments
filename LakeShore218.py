"""
device controll class for the LakeShore Temperature Monitor Model 218
so far only used on device with serial: 21EB3L
"""

import serial
import TangoHelper


class LakeShore218:
    def __init__(self, serial_number='21EB3L'):
        self.serial_number = serial_number
        self.ser = serial.Serial()

    def connect(self):
        if self.ser.is_open:
            print('device already connected')
            return

        self.ser = serial.Serial(baudrate=9600,
                                 timeout=1,
                                 bytesize=7,
                                 parity='O',
                                 stopbits=1)

        TangoHelper.connect_by_serial_number(self.ser, self.serial_number)

    def disconnect(self):
        self.ser.close()
        print('connection closed')

    def read_temp(self, sensor):
        """read temperature of specified sensor (can be 1-8)"""
        self.ser.write(('KRDG? %s\n' % sensor).encode())
        return self.ser.readline().decode().strip().strip('+')

    def log_start(self, continue_last_log=False, interval=20, overwrite_at_full_memory=True, number_of_readings=2):
        """start internal temperature logging

        interval in s
        StorageCapability per Readings: (1500/1, 1000/2, 750/3, 600/4 ...) more details in the Manual
        """

        self.ser.write(('LOGSET 1 %d %d %d %d\n' %
                        (overwrite_at_full_memory, continue_last_log, interval, number_of_readings)).encode())
        self.ser.readline()  # wait for LOGSET command to finish

        self.ser.write('LOG 1\n'.encode())
        self.ser.readline()  # wait for LOG command to finish

    def log_stop(self):
        self.ser.write('LOG 0\n'.encode())
        self.ser.readline()  # wait for LOG command to finish

    def log_read(self, sensors=None):
        if sensors is None:  # avoiding list as default value (mutable)
            sensors = [1, 2]

        self.ser.write('LOGNUM ?\n'.encode())
        last_record_number = int(self.ser.readline().decode().strip())

        data = {'date,time': []}
        for sensor_id in sensors:
            data['sensor%d' % sensor_id] = []

        for record_number in range(1, last_record_number + 1):

            date_time = ''

            for sensor_id in sensors:
                self.ser.write(('LOGVIEW? %d %d\n' % (record_number, int(sensor_id))).encode())
                record = self.ser.readline().decode().split(',')

                if int(record[3]) != 0:
                    print('WARNING: error code %s returned on sensor %s' % (record[3], sensor_id))
                if int(record[4]) != 1:
                    print('WARNING: temperature unit of sensor %s is not Kelvin!' % sensor_id)

                date_time = record[0] + ',' + record[1]
                data['sensor%d' % sensor_id].append(record[2].strip('+'))
            else:
                data['date,time'].append(date_time)

        return data

    def log_status(self):
        self.ser.write('LOG?\n'.encode())
        return self.ser.readline().decode().strip()
