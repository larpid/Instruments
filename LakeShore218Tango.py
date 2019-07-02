"""
Tango Server for the LakeShore Temperature Monitor Model 218
so far only used on device with serial: 21EB3L
"""

from LakeShore218 import LakeShore218
import sys
from tango import AttrWriteType, DispLevel
from PyTango import DevState, DebugIt, CmdArgType
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, pipe
from TangoHelper import StoreStdOut


def command2(command_function):
    command_function = command(command_function)
    attribute_name = 'cmd_%s' % command_function.__name__
    print(attribute_name)
    return command_function, attribute(), command_function


class LakeShore218Tango(Device, metaclass=DeviceMeta):

    def __init__(self, cl, name):
        Device.__init__(self, cl, name)
        self.debug_stream("In " + self.get_name() + ".__init__()")
        LakeShore218Tango.init_device(self)
        self.lake_shore = LakeShore218()
        self.random_variable = 26.8
        self.new_attr = attribute()  # this seems to not work... :/
        #print(dir(self))
        for attr in dir(self):
            #if getattr(self, attr)
            print(attr, type(getattr(self, attr)))
        #print(self.__dir__())
        print('....')
        #print(list(map(type, dir(self))))

        def dummy_func():
            return 42
        self.read_new_attr = dummy_func

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.OFF)
        # redirect stdout to store last line
        sys.stdout = StoreStdOut()

    @command2
    def connect(self):
        self.set_state(DevState.INIT)
        if self.lake_shore.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    def disconnect(self):
        self.lake_shore.disconnect()
        self.set_state(DevState.OFF)

    disconnect, attr1, read_attr1 = command2(disconnect)

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
