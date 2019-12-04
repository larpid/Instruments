"""
Tango Server for the VACOM MVC3 vacuum gauge controller
"""

from MVC3GaugeController import MVC3GaugeController
import sys
from serial.serialutil import SerialException
from tango import AttrWriteType
from PyTango import DevState
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import device_property
from PyTango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


class MVC3GaugeControllerTango(Device, metaclass=DeviceMeta):

    serial_address = device_property(dtype=float)  # store address in decimal (can be 1 - 126)

    def init_device(self):
        sys.stdout = StoreStdOut()
        self.mvc3 = MVC3GaugeController(self.serial_address)
        self.set_state(DevState.OFF)
        self.connect()  # try to auto connect on server start. can also be done manually

    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read_stored_message()

    @command
    def connect(self):
        self.set_state(DevState.INIT)
        if self.mvc3.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    cmd_connect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_connect(self, _):
        self.connect()

    @command
    def disconnect(self):
        self.mvc3.disconnect()
        self.set_state(DevState.OFF)

    cmd_disconnect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_disconnect(self, _):
        self.disconnect()

    @attribute(dtype=float, unit='mBar', access=AttrWriteType.READ)
    def P1(self):
        return self.mvc3.read_pressure(1)

    @attribute(dtype=float, unit='mBar', access=AttrWriteType.READ)
    def P2(self):
        return self.mvc3.read_pressure(2)

    @attribute(dtype=float, unit='mBar', access=AttrWriteType.READ)
    def P3(self):
        return self.mvc3.read_pressure(3)


if __name__ == "__main__":
    run([MVC3GaugeControllerTango])
