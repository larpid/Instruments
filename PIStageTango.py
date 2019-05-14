"""
Tango Server for the linear delay stage
so far only used on stage with serial: 117018374
"""

import PIStage
import sys
from tango import AttrWriteType, DispLevel
from PyTango import DevState, DebugIt, CmdArgType
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, pipe


class PIStageTango(Device, metaclass=DeviceMeta):

    controller_serial_number = sys.argv[1]
    stage = PIStage.PIStage(controller_serial=controller_serial_number)
    move_step_size = 0.001

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.OFF)

    cmd_connect = attribute(access=AttrWriteType.WRITE)

    @command
    def connect(self):
        self.set_state(DevState.INIT)
        if self.stage.connect():
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    def write_cmd_connect(self, _):
        self.connect()

    cmd_disconnect = attribute(access=AttrWriteType.WRITE)

    @command
    def disconnect(self):
        self.stage.disconnect()
        self.set_state(DevState.OFF)

    def write_cmd_disconnect(self, _):
        self.disconnect()

    @attribute(dtype=str)
    def controller_serial(self):
        return self.controller_serial_number

    position = attribute(label="Position relative to set zero point", dtype=float,
                         display_level=DispLevel.EXPERT,
                         access=AttrWriteType.READ,
                         unit="mm",
                         min_value=stage.position_min, max_value=stage.position_max)

    def read_position(self):
        return self.stage.position_get()

    position_um = attribute(label="Position relative to set zero point", dtype=float,
                            display_level=DispLevel.EXPERT,
                            access=AttrWriteType.READ,
                            unit="um",
                            min_value=stage.position_min, max_value=stage.position_max)

    def read_position_um(self):
        return self.stage.position_get()*1000.0  # unit conversion [mm -> um]

    position_unshifted_um = attribute(label="absolute position", dtype=float,
                                      display_level=DispLevel.EXPERT,
                                      access=AttrWriteType.READ,
                                      unit="um",
                                      min_value=stage.position_min * 1000.0,
                                      max_value=stage.position_max * 1000.0)

    def read_position_unshifted_um(self):
        return self.stage.position_unshifted_get() * 1000.0  # unit conversion [mm -> um]

    cmd_move_absolute = attribute(access=AttrWriteType.WRITE,
                                  dtype=float,
                                  unit="mm")

    @command(dtype_in=float)
    def move_absolute(self, new_pos):
        self.set_state(DevState.MOVING)
        self.stage.move_absolute(new_pos)

    def write_cmd_move_absolute(self, new_pos):
        self.move_absolute(new_pos)

    cmd_move_absolute_um = attribute(access=AttrWriteType.WRITE,
                                     dtype=float,
                                     unit="um")

    @command(dtype_in=float)
    def move_absolute_um(self, new_pos_um):
        new_pos_mm = new_pos_um / 1000.0
        self.move_absolute(new_pos_mm)

    def write_cmd_move_absolute_um(self, new_pos):
        self.move_absolute_um(new_pos)

    cmd_move_relative_um = attribute(access=AttrWriteType.WRITE,
                                     dtype=float,
                                     unit="um")

    @command(dtype_in=float)
    def move_relative_um(self, step_um):
        step_mm = step_um/1000.0
        self.move_relative(step_mm)

    def write_cmd_move_relative_um(self, step_um):
        self.move_relative_um(step_um)

    @attribute(dtype=bool)
    def on_target_state(self):
        if self.stage.on_target_state():
            self.set_state(DevState.ON)
            return True
        else:
            return False

    @attribute(dtype=float)
    def position_min_um(self):
        return self.stage.position_min * 1000.0  # unit conversion [mm -> um]

    @attribute(dtype=float)
    def position_max_um(self):
        return self.stage.position_max * 1000.0  # unit conversion [mm -> um]

    velocity = attribute(label="Velocity", dtype=float,
                         display_level=DispLevel.EXPERT,
                         access=AttrWriteType.READ_WRITE,
                         unit="mm/s",
                         fget="get_velocity",
                         fset="set_velocity",
                         doc="stage position")

    def get_velocity(self):
        return self.stage.velocity

    def set_velocity(self, velocity):
        self.stage.pi_set_velocity(velocity)

    velocity_umps = attribute(label="Velocity", dtype=float,
                              display_level=DispLevel.EXPERT,
                              access=AttrWriteType.READ_WRITE,
                              unit="um/s",
                              fget="get_velocity_umps",
                              fset="set_velocity_umps",
                              doc="stage position")

    def get_velocity_umps(self):
        return self.stage.velocity * 1000.0  # unit conversion [mm/s -> um/s]

    def set_velocity_umps(self, velocity_umps):
        velocity_mmps = velocity_umps / 1000.0
        self.stage.pi_set_velocity(velocity_mmps)

    cmd_set_zero_position = attribute(access=AttrWriteType.WRITE)

    @command
    def set_zero_position(self):
        self.stage.set_zero_position()

    def write_cmd_set_zero_position(self, _):
        self.set_zero_position()

    cmd_zero_reference_move = attribute(access=AttrWriteType.WRITE)

    @command
    def zero_reference_move(self):
        self.stage.pi_zero_reference_move()
        self.stage.pi_handle_limits()

    def write_cmd_zero_reference_move(self, _):
        self.zero_reference_move()

    cmd_stop_motion = attribute(access=AttrWriteType.WRITE)

    @command
    def stop_motion(self):
        self.stage.pi_stop_motion()
        self.set_state(DevState.ON)

    def write_cmd_stop_motion(self, _):
        self.stop_motion()

    @attribute(dtype=str)
    def last_error(self):
        return str(self.stage.last_error)

    cmd_move_step = attribute(access=AttrWriteType.WRITE,
                              dtype=float,
                              label="moves stage by pregiven step in input direction",
                              doc="moves stage by pregiven step in input direction")

    @command(dtype_in=float)
    def move_step(self, direction):
        self.set_state(DevState.MOVING)
        if direction >= 0:
            self.stage.move_relative(self.move_step_size)
        else:
            self.stage.move_relative(-1 * self.move_step_size)

    def write_cmd_move_step(self, direction):
        self.move_step(direction)

    @attribute(dtype=float,
               access=AttrWriteType.READ_WRITE)
    def move_step_size_um(self):
        return self.move_step_size * 1000.0

    def write_move_step_size_um(self, step_um):
        self.move_step_size = step_um / 1000.0


if __name__ == "__main__":
    run([PIStageTango])
