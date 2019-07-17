"""
Tango Server for the LakeShore Temperature Monitor Model 218
so far only used on device with serial: 21EB3L
"""

from LakeShore218 import LakeShore218
import sys
from tango import AttrWriteType, DispLevel
from PyTango import DevState, DebugIt, CmdArgType, Attr, Util
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


class LakeShore218Tango(Device, metaclass=DeviceMeta):

    def init_device(self):
        sys.stdout = StoreStdOut()
        self.lake_shore = LakeShore218(sys.argv[1])

        # default log options can be changed via attributes
        self.log_options = {'continue_last_log': False,
                            'interval': 20,  # time steps in s
                            'overwrite_at_full_memory': True,
                            'number_of_readings': 2}  # number of logged channels (/logged sensors)

        self.set_state(DevState.OFF)
        self.connect()  # try to auto connect on server start. can also be done manually

    @attribute
    def read_temp_sensor1(self):
        return self.lake_shore.read_temp(1)

    @attribute
    def read_temp_sensor2(self):
        return self.lake_shore.read_temp(2)

    @attribute
    def read_temp_sensor3(self):
        return self.lake_shore.read_temp(3)

    @attribute
    def read_temp_sensor4(self):
        return self.lake_shore.read_temp(4)

    @attribute
    def read_temp_sensor5(self):
        return self.lake_shore.read_temp(5)

    @attribute
    def read_temp_sensor6(self):
        return self.lake_shore.read_temp(6)

    @attribute
    def read_temp_sensor7(self):
        return self.lake_shore.read_temp(7)

    @attribute
    def read_temp_sensor8(self):
        return self.lake_shore.read_temp(8)

    @command
    def connect(self):
        self.set_state(DevState.INIT)
        if self.lake_shore.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    cmd_connect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_connect(self, _):
        self.connect()

    @command
    def disconnect(self):
        self.lake_shore.disconnect()
        self.set_state(DevState.OFF)

    cmd_disconnect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_disconnect(self, _):
        self.disconnect()

    log_continue_last = attribute(access=AttrWriteType.READ_WRITE,
                                  dtype=bool)

    def read_log_continue_last(self):
        return self.log_options['continue_last_log']

    def write_log_continue_last(self, continue_last_log):
        self.log_options['continue_last_log'] = continue_last_log

    log_interval = attribute(access=AttrWriteType.READ_WRITE,
                             unit='s')

    def read_log_interval(self):
        return self.log_options['interval']

    def write_log_interval(self, interval):
        self.log_options['interval'] = interval

    log_overwrite_at_full_memory = attribute(access=AttrWriteType.READ_WRITE,
                                             dtype=bool)

    def read_log_overwrite_at_full_memory(self):
        return self.log_options['overwrite_at_full_memory']

    def write_log_overwrite_at_full_memory(self, overwrite_at_full_memory):
        self.log_options['overwrite_at_full_memory'] = overwrite_at_full_memory

    log_number_of_readings = attribute(access=AttrWriteType.READ_WRITE,
                                       dtype=int)

    def read_log_number_of_readings(self):
        return self.log_options['number_of_readings']

    def write_log_number_of_readings(self, number_of_readings):
        self.log_options['number_of_readings'] = number_of_readings

    @command
    def log_start(self):
        self.lake_shore.log_start(**self.log_options)

    cmd_log_start = attribute(access=AttrWriteType.WRITE)

    def write_cmd_log_start(self, _):
        self.log_start()

    @command
    def log_stop(self):
        self.lake_shore.log_stop()

    cmd_log_stop = attribute(access=AttrWriteType.WRITE)

    def write_cmd_log_stop(self, _):
        self.log_stop()

    @pipe
    def log_read(self):
        """read the log
        used sensors are a range created from the number_of_readings setting in log_options
        """

        sensor_list = list(range(1, self.log_options['number_of_readings'] + 1))
        dict_of_sensor_temp_lists = self.lake_shore.log_read(sensor_list)

        return 'temperature log', dict_of_sensor_temp_lists

    @attribute
    def log_status(self):
        return self.lake_shore.log_status()

    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read_stored_message()


if __name__ == "__main__":
    run([LakeShore218Tango])
