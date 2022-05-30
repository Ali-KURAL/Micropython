from machine import I2C,Pin
import time
from tps63811 import TPS63811

tps = TPS63811(0,scl = 17,sda = 16)
tps.rng = 1
tps.out_2 = 3500

tps.enable = True
while True:
    print(tps.out_1)
    print(tps.out_2)
    time.sleep(1)