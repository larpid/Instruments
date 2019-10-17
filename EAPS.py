"""
device controll class for the Elektro-Automatik PS2342-10B Power Supply
so far only used on device with serial: 2845070119
"""

import serial
import TangoHelper
import struct

# communication object data types known by eaps device (for reading stuff):
communication_object_data_types = {0: str,  # read only, device type
                                   1: str,  # ro, S/N
                                   2: lambda x: struct.unpack('>f', x)[0],  # ro, nominal voltage
                                   3: lambda x: struct.unpack('>f', x)[0],  # ro, nominal current
                                   4: lambda x: struct.unpack('>f', x)[0],  # ro, nominal power
                                   6: str,  # ro, device article no.
                                   8: str,  # ro, manufacturer
                                   9: str,  # ro, software version
                                   19: int,  # ro, device class
                                   38: int,  # read write, OVP threshold (OVP is probably overvoltage)
                                   39: int,  # rw, OCP threshold (OCP is probably overcurrent)
                                   50: int,  # rw, set value voltage U (% of U nominal * 256)
                                   51: int,  # rw, set value current I (% of I nominal * 256)
                                   54: chr,  # rw, control commands
                                   71: lambda x: [x[:2],
                                                  struct.unpack('>h', x[2:4])[0],
                                                  struct.unpack('>h', x[4:])[0]],  # ro, request Status + actual values
                                   72: lambda x: [x[:2],
                                                  struct.unpack('>h', x[2:4])[0],
                                                  struct.unpack('>h', x[4:])[0]],  # ro, request Status + set values
                                   255: int  # error object
                                   }

# error messages known by eaps device
error_messages = {3: "Check sum incorrect",
                  4: "Start delimiter incorrect",
                  5: "Wrong address for output",
                  7: "Object not defined",
                  8: "Object length incorrect",
                  9: "Read/Write permissions violated, no access",
                  15: "Device is in \"Lock\" state",
                  48: "Upper limit of object exceeded",
                  49: "Lower limit of object exceeded"
                  }


def decode_eaps_answer(answer):
    """used to decode messages from eaps device to pc"""
    if len(answer) < 5:
        print('received message incorrect (too short)')
        return
    start_delimiter = answer[0]
    device_node = answer[1]+1
    communication_object = answer[2]
    data = answer[3:-2]
    checksum = answer[-2] * 2 ** 8 + answer[-1]  # checksum gets sent as hex number in 2 bytes, variable is int

    # check for correct checksum
    expected_checksum = sum(answer[:-2]) % 2 ** 16  # gives int checksum displayable in 2 bytes
    if checksum != expected_checksum:
        raise ValueError('wrong checksum: %s received when %s expected' % (checksum, expected_checksum))

    if len(data) != start_delimiter % 2 ** 4 + 1:
        raise SyntaxError('unexpected data length')

    if communication_object == 255:
        if ord(data) == 0:
            return device_node, communication_object, True

        elif ord(data) in [8, 9, 15, 48, 49]:
            raise RuntimeWarning('device Reports Warning code %s: %s' % (data, error_messages[ord(data)]))
        else:
            raise RuntimeError('device Reports Error code %s: %s' % (data, error_messages[ord(data)]))

    received_value = communication_object_data_types[communication_object](data)
    return device_node, communication_object, received_value


def encode_eaps_message(channel, message_is_request, message_object, message):
    """build messages to be sent from pc to eaps device
    inputs data types: int or str, boolean, int (decimal), bytes or str"""

    if type(message) is not bytes:
        message = message.encode()

    # build start delimiter
    start_delimiter_hex_value = 2**6 + 2**5 + 2**4  # set certain bits
    if not message_is_request:
        start_delimiter_hex_value += 2**7

    if len(message) > 16:
        raise ValueError('message: \'%s\' too long' % message)
    elif len(message) > 0:
        start_delimiter_hex_value += len(message)-1

    encoded_message_without_checksum = \
        bytes([start_delimiter_hex_value]) + \
        bytes([int(channel)-1]) + \
        bytes([message_object]) + \
        message

    checksum = sum(encoded_message_without_checksum) % 2 ** 16  # gives int checksum displayable in 2 bytes

    return encoded_message_without_checksum + bytes([checksum//2**8, checksum % 2**8])


class EAPS:
    def __init__(self, serial_number='2845070119'):
        self.serial_number = serial_number
        self.ser = serial.Serial()
        self.nominal_voltage = 0  # in V
        self.nominal_current = 0  # in A
        self.nominal_power = 0  # in W

    def connect(self):
        if self.ser.is_open:
            print('device already connected')
            return

        self.ser = serial.Serial(baudrate=115200,
                                 timeout=1,
                                 bytesize=8,
                                 parity='O',
                                 stopbits=1)

        def idn_answer_check_function(idn_line, serial_number):
            if idn_line[3:-3].decode() == serial_number:  # data lies in idn_line[3:-2] but last character is \x00
                _, _, _ = decode_eaps_answer(idn_line)  # just to check for errors
                return True
            else:
                return False

        TangoHelper.connect_by_serial_number(self.ser, self.serial_number, idn_message='\x70\x01\x01\x00\x72',
                                             idn_answer_check_function=idn_answer_check_function)

        # read nominal values
        self.ser.write(encode_eaps_message(1, True, 2, ''))
        _, _, self.nominal_voltage = decode_eaps_answer(self.ser.readline())
        print('nominal voltage is %s' % self.nominal_voltage)
        self.ser.write(encode_eaps_message(1, True, 3, ''))
        _, _, self.nominal_current = decode_eaps_answer(self.ser.readline())
        print('nominal current is %s' % self.nominal_current)
        self.ser.write(encode_eaps_message(1, True, 4, ''))
        _, _, self.nominal_power = decode_eaps_answer(self.ser.readline())
        print('nominal power is %s' % self.nominal_power)

    def disconnect(self):
        self.ser.close()
        print('connection closed')

    def switch_to_remote_control(self, channel):
        self.ser.write(encode_eaps_message(channel, False, 54, '\x10\x10'))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s switched to remote controlled operation' % channel)
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def switch_to_manual_control(self, channel):
        self.ser.write(encode_eaps_message(channel, False, 54, '\x10\x00'))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s switched to manual controlled operation' % channel)
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def switch_output_on(self, channel):
        self.ser.write(encode_eaps_message(channel, False, 54, '\x01\x01'))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s switched power output on' % channel)
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def switch_output_off(self, channel):
        self.ser.write(encode_eaps_message(channel, False, 54, '\x01\x00'))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s switched power output off' % channel)
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def write_set_voltage(self, channel, voltage):
        """writes voltage set value (in V) of given channel"""
        # convert voltage to message (with bit shift and percentage conversion according to manual):
        encoded_voltage = int(round(voltage/self.nominal_voltage*256*100))
        byte_encoded_voltage = bytes([encoded_voltage//256, encoded_voltage % 256])
        self.ser.write(encode_eaps_message(channel, False, 50, byte_encoded_voltage))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s has new set voltage of %sV' % (channel, voltage))
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def write_set_current(self, channel, current):
        """writes current set value (in A) of given channel"""
        # convert current to message (with bit shift and percentage conversion according to manual):
        encoded_current = int(round(current/self.nominal_current*256*100))
        byte_encoded_current = bytes([encoded_current//256, encoded_current % 256])
        self.ser.write(encode_eaps_message(channel, False, 51, byte_encoded_current))
        if decode_eaps_answer(self.ser.readline()) == (int(channel), 255, True):
            print('channel %s has new set current of %sA' % (channel, current))
            return True
        else:
            print('answer unexpected, device state unknown')
            return False

    def read_status_plus_actual_values(self, channel):
        self.ser.write(encode_eaps_message(channel, True, 71, b''))
        _, _, answer = decode_eaps_answer(self.ser.readline())

        print(answer)
        status = {'remote_controlled': bool(answer[0][0] & 1),  # otherwise free access
                  'output_on': bool(answer[0][1] & 1),
                  'control_state': None,
                  'tracking_active': bool(answer[0][1] & 8),
                  'OVP_active': bool(answer[0][1] & 16),
                  'OCP_active': bool(answer[0][1] & 32),
                  'OPP_active': bool(answer[0][1] & 64),
                  'OTP_active': bool(answer[0][1] & 127)}

        if answer[0][1] & 6:
            status['control_state'] = 'CC'
        else:
            status['control_state'] = 'CV'

        actual_voltage = answer[1]/(256*100)*self.nominal_voltage  # requires bit shift, percentage calc and normalizing
        actual_current = answer[2]/(256*100)*self.nominal_current  # requires bit shift, percentage calc and normalizing

        return status, actual_voltage, actual_current

    def read_status_plus_set_values(self, channel):
        self.ser.write(encode_eaps_message(channel, True, 72, b''))
        _, _, answer = decode_eaps_answer(self.ser.readline())

        print(answer)
        status = {'remote_controlled': bool(answer[0][0] & 1),  # otherwise free access
                  'output_on': bool(answer[0][1] & 1),
                  'control_state': None,
                  'tracking_active': bool(answer[0][1] & 8),
                  'OVP_active': bool(answer[0][1] & 16),
                  'OCP_active': bool(answer[0][1] & 32),
                  'OPP_active': bool(answer[0][1] & 64),
                  'OTP_active': bool(answer[0][1] & 128)}

        if answer[0][1] & 6:
            status['control_state'] = 'CC'
        else:
            status['control_state'] = 'CV'

        set_voltage = answer[1]/(256*100)*self.nominal_voltage  # requires bit shift, percentage calc and normalizing
        set_current = answer[2]/(256*100)*self.nominal_current  # requires bit shift, percentage calc and normalizing

        return status, set_voltage, set_current
