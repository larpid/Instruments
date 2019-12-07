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

    serial_address = device_property(dtype=int,  # store address in decimal (can be 1 - 126)
                                     default_value=1,
                                     doc="this is the devices serial address in decimal. Connection on this device is "
                                         "not done by asking for the serial number (not supported by device) but by "
                                         "asking for the RS485 Serial Address (can also be set/requested in the here "
                                         "used RS232 mode). These were manually set with SSA (e.g. 'RSA46\r' sets this "
                                         "to hex value 46 which is 70 in decimal) command and are labeled on the case "
                                         "of each device. IMPORTANT: after setting the serial address the device must "
                                         "be switched to RS485 and can then be switched back to RS232 immediately. "
                                         "Otherwise the address will reset on next device restart")

    pressure_decimal_places = device_property(dtype=int,
                                              default_value=2,
                                              doc="number of displayed decimal places on pressure readings")

    def init_device(self):
        sys.stdout = StoreStdOut()
        self.get_device_properties()  # otherwise self.serial will be None
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

    @attribute(dtype=str, #unit='mBar',
               access=AttrWriteType.READ)
    def P1(self):
        """writes out errors and info too"""
        return self.mvc3.read_pressure(1, decimal_places=self.pressure_decimal_places)

    @attribute(dtype=str, unit='mBar', access=AttrWriteType.READ)
    def P2(self):
        """writes out errors and info too"""
        return self.mvc3.read_pressure(2, decimal_places=self.pressure_decimal_places)

    @attribute(dtype=str, unit='mBar', access=AttrWriteType.READ)
    def P3(self):
        """writes out errors and info too"""
        return self.mvc3.read_pressure(3, decimal_places=self.pressure_decimal_places)


if __name__ == "__main__":
    run([MVC3GaugeControllerTango])
