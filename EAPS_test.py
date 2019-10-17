'''temporary test file'''

import EAPS, time

test = EAPS.EAPS('2845070119')
test.connect()
test.switch_to_remote_control(1)
test.switch_output_on(1)
test.write_set_voltage(1, 5)
print(test.read_status_plus_actual_values(1))
print(test.read_status_plus_set_values(1))
time.sleep(1)
test.switch_output_off(1)
print(test.read_status_plus_actual_values(1))
print(test.read_status_plus_set_values(1))


test.switch_to_manual_control(1)
test.disconnect()
