"""
Tango Server for the LakeShore Temperature Monitor Model 218
so far only used on device with serial: 21EB3L
"""

from LakeShore218 import LakeShore218
import sys
from tango import AttrWriteType, DispLevel
import PyTango
from PyTango import DevState, DebugIt, CmdArgType, Attr, Util
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


class LakeShore218Tango(Device, metaclass=DeviceMeta):

    def __init__(self, cl, name):
        Device.__init__(self, cl, name)
        self.debug_stream("In " + self.get_name() + ".__init__()")
        self.lake_shore = None  # init in init_device
        # default log options can be changed via attribute
        self.log_options = {'continue_last_log': False,
                            'interval': 20,  # time steps in s
                            'overwrite_at_full_memory': True,
                            'number_of_readings': 2}  # number of logged channels (/logged sensors)
        LakeShore218Tango.init_device(self)

    def init_device(self):
        Device.init_device(self)
        sys.stdout = StoreStdOut()
        self.lake_shore = LakeShore218(sys.argv[1])
        self.set_state(DevState.OFF)

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

    @attribute(access=AttrWriteType.READ)
    def read_temp(self, sensor_id):
        return self.lake_shore.read_temp(sensor_id)

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

    log_number_of_readings = attribute(access=AttrWriteType.READ_WRITE)

    def read_log_number_of_readings(self):
        return self.log_options['number_of_readings']

    def write_log_number_of_readings(self, number_of_readings):
        self.log_options['number_of_readings'] = number_of_readings

    @command
    def log_start(self):
        #self.lake_shore.log_start(continue_last_log=self.log_options['continue_last_log'],
        #                          interval=self.log_options['interval'],
        #                          overwrite_at_full_memory=self.log_options['overwrite_at_full_memory'],
        #                          number_of_readings=self.log_options['number_of_readings']
        # todo: if this line works remove the 4 lines before
        self.lake_shore.log_start(**self.log_options)

    @command
    def log_stop(self):
        self.lake_shore.log_stop()

    log_read = attribute(AttrWriteType.READ)

    def read_log_read(self):
        """reading the log currently hardcoded to use channel 1 and 2"""
        return self.lake_shore.log_read([1, 2])

    log_status = attribute(AttrWriteType.READ)

    def read_log_status(self):
        return self.lake_shore.log_status()

    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read()


if __name__ == "__main__":
    run([LakeShore218Tango])
