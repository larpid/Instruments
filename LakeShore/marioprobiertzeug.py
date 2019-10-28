
from pathlib import Path
import time

my_file = Path('/media/chamber7/Data/TEMP_TDC_test/lakeShore.txt')

if my_file.is_file():
    print('jo')
    time.sleep(5)
else:
    print('no')



