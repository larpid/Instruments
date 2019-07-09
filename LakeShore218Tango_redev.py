"""
DEVELOPMENT FILE, DO NOT USE THIS ONE

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

    def command2(self, *decorator_args, **decorator_kwargs):
        def inside_command2(command_function):
            command_function = command(command_function, *decorator_args, **decorator_kwargs)
            attribute_name = 'cmd_%s' % command_function.__name__
            attr = Attr(attribute_name, PyTango.DevDouble)
            self.add_attribute(attr, r_meth=None, w_meth=command_function)

        return inside_command2

    def __init__(self, cl, name):
        Device.__init__(self, cl, name)
        self.debug_stream("In " + self.get_name() + ".__init__()")
        self.lake_shore = None  # init in init_device
        LakeShore218Tango.init_device(self)



        def r_testattr_22(attr):
            return 22
        # redirect stdout to store last line

        def dummy_func():
            return 42
        self.read_new_attr = dummy_func

    def init_device(self):
        Device.init_device(self)
        sys.stdout = StoreStdOut()
        self.lake_shore = LakeShore218(sys.argv[1])
        self.set_state(DevState.OFF)



    @command2(dtype_in=float)
    def connect(self):
        self.set_state(DevState.INIT)
        if self.lake_shore.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    def disconnect(self):
        self.lake_shore.disconnect()
        self.set_state(DevState.OFF)

    disconnect = command2(disconnect)

    def r_testattr_22(self, attr):
        attr.set_value(22.0)

    testcomm = command()

#temp1
#temp2
#logstart
#logstop
#logcontinue
#logread
#logstatus


    @attribute(dtype=str)
    def server_message(self):
        return sys.stdout.read()


if __name__ == "__main__":
    run([LakeShore218Tango])
