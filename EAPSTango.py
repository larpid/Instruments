"""
Tango Server for the Elektro-Automatik PS2342-10B Power Supply
so far only used on device with serial: 2845070119
"""

from EAPS import EAPS
import sys
from serial.serialutil import SerialException
from tango import AttrWriteType, AttrQuality
from PyTango import DevState, DebugIt, CmdArgType, Attr, Util
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


class EAPSTango(Device, metaclass=DeviceMeta):

    def init_device(self):
        sys.stdout = StoreStdOut()
        self.eaps = EAPS(sys.argv[1])

        # space for instance variables

        self.set_state(DevState.OFF)
        self.connect()  # try to auto connect on server start. can also be done manually

    @command
    def connect(self):
        self.set_state(DevState.INIT)
        if self.eaps.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    cmd_connect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_connect(self, _):
        self.connect()

    @command
    def disconnect(self):
        self.eaps.disconnect()
        self.set_state(DevState.OFF)

    cmd_disconnect = attribute(access=AttrWriteType.WRITE)

    def write_cmd_disconnect(self, _):
        self.disconnect()

    c1_remote_control_active = attribute(access=AttrWriteType.WRITE,
                                      dtype=bool)

    def write_c1_remote_control_active(self, new_status):
        if new_status:
            self.eaps.switch_to_remote_control(1)
        else:
            self.eaps.switch_to_manual_control(1)

    c2_remote_control_active = attribute(access=AttrWriteType.WRITE,
                                         dtype=bool)

    def write_c2_remote_control_active(self, new_status):
        if new_status:
            self.eaps.switch_to_remote_control(2)
        else:
            self.eaps.switch_to_manual_control(2)

    c1_output_on = attribute(access=AttrWriteType.WRITE,
                             dtype=bool)

    def write_c1_output_on(self, new_status):
        if new_status:
            self.eaps.switch_output_on(1)
        else:
            self.eaps.switch_output_off(1)

    c2_output_on = attribute(access=AttrWriteType.WRITE,
                             dtype=bool)

    def write_c2_output_on(self, new_status):
        if new_status:
            self.eaps.switch_output_on(2)
        else:
            self.eaps.switch_output_off(2)

    c1_set_voltage = attribute(access=AttrWriteType.WRITE,
                               dtype=float)

    def write_c1_set_voltage(self, voltage):
        self.eaps.write_set_voltage(1, voltage)

    c2_set_voltage = attribute(access=AttrWriteType.WRITE,
                               dtype=float)

    def write_c2_set_voltage(self, voltage):
        self.eaps.write_set_voltage(2, voltage)

    c1_set_current = attribute(access=AttrWriteType.WRITE,
                               dtype=float)

    def write_c1_set_current(self, current):
        self.eaps.write_set_current(1, current)

    c2_set_current = attribute(access=AttrWriteType.WRITE,
                               dtype=float)

    def write_c2_set_current(self, current):
        self.eaps.write_set_current(2, current)

    @pipe
    def c1_status_plus_actual_values(self):
        """read status info plus voltage and current on output 1
        this is not implemented separate for all values due to the devices ask-all-in-one-request
        communication protocol and it's slow response times
        """

        status, actual_voltage, actual_current = self.eaps.read_status_plus_actual_values(1)

        return 'status_plus_actual_values', {**status,
                                             'actual_voltage': actual_voltage,
                                             'actual_current': actual_current}

    @pipe
    def c2_status_plus_actual_values(self):
        """read status info plus voltage and current on output 2
        this is not implemented separate for all values due to the devices ask-all-in-one-request
        communication protocol and it's slow response times
        """

        status, actual_voltage, actual_current = self.eaps.read_status_plus_actual_values(2)

        return 'status_plus_actual_values', {**status,
                                             'actual_voltage': actual_voltage,
                                             'actual_current': actual_current}

    @pipe
    def c1_status_plus_set_values(self):
        """read status info plus voltage and current (set values) on output 1
        this is not implemented separate for all values due to the devices ask-all-in-one-request
        communication protocol and it's slow response times
        """

        status, set_voltage, set_current = self.eaps.read_status_plus_set_values(1)

        return 'status_plus_set_values', {**status,
                                          'set_voltage': set_voltage,
                                          'set_current': set_current}

    @pipe
    def c2_status_plus_set_values(self):
        """read status info plus voltage and current (set values) on output 2
        this is not implemented separate for all values due to the devices ask-all-in-one-request
        communication protocol and it's slow response times
        """

        status, set_voltage, set_current = self.eaps.read_status_plus_set_values(2)

        return 'status_plus_set_values', {**status,
                                          'set_voltage': set_voltage,
                                          'set_current': set_current}

    @attribute(dtype=float, unit='U')
    def c1_actual_voltage(self):
        if self.get_state() == DevState.ON:
            try:
                _, voltage, _ = self.eaps.read_status_plus_actual_values(1)
                return voltage
            except SerialException:
                self.set_state(DevState.FAULT)
                self.eaps.disconnect()
                print('ERROR: port not open')

    @attribute(dtype=float, unit='U')
    def c2_actual_voltage(self):
        if self.get_state() == DevState.ON:
            try:
                _, voltage, _ = self.eaps.read_status_plus_actual_values(2)
                return voltage
            except SerialException:
                self.set_state(DevState.FAULT)
                self.eaps.disconnect()
                print('ERROR: port not open')

    @attribute(dtype=float, unit='A')
    def c1_actual_current(self):
        if self.get_state() == DevState.ON:
            try:
                _, _, current = self.eaps.read_status_plus_actual_values(1)
                return current
            except SerialException:
                self.set_state(DevState.FAULT)
                self.eaps.disconnect()
                print('ERROR: port not open')

    @attribute(dtype=float, unit='A')
    def c2_actual_current(self):
        if self.get_state() == DevState.ON:
            try:
                _, _, current = self.eaps.read_status_plus_actual_values(2)
                return current
            except SerialException:
                self.set_state(DevState.FAULT)
                self.eaps.disconnect()
                print('ERROR: port not open')

    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read_stored_message()


if __name__ == "__main__":
    run([EAPSTango])
