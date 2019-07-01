import LakeShore218
import time

test = LakeShore218.LakeShore218()
test.connect()

print(test.log_status())
#for i in range(9):
#    print(test.read_temp(i))
print('_')
test.log_start(continue_last_log=False, interval=1)
print('_')
print(test.log_status())
print('_')
print(test.log_status())
print('recording...')
time.sleep(1)
test.log_stop()
print(test.log_read([1, 2]))
print(test.log_status())

test.disconnect()
