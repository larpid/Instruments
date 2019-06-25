import LakeShore
import time

test = LakeShore.LakeShore()
test.connect()

#print(test.log_status())
#for i in range(9):
#    print(test.read_temp(i))
#time.sleep(1)
test.log_start(False, 1)
#time.sleep(1)
#print(test.log_status())
print('recording...')
time.sleep(5)
test.log_stop()
#time.sleep(1)
print(test.log_read([1, 2]))
print(test.log_status())

test.disconnect()
