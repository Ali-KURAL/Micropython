from ds3231 import DS3231
import machine
import time

# initialize DS3231
rtc = DS3231(0,17, 16)

# set time to 2022, June, 1, Wednesday, 18 h, 10 min, 0 sec
rtc.setDateTime(22, 6, 1, 3, 18, 10, 0)

# print current time for 5 seconds
while True:
    print(rtc.getDateTime())
    time.sleep(1)
    
