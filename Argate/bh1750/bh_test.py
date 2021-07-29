import machine
from bh_1750 import BH1750
import time

scl = machine.Pin(17)
sda = machine.Pin(16)
i2c = machine.I2C(0,scl = scl,sda = sda)

s = BH1750(i2c)
s.set_mode("CLR")


while True:
    lux = s.lux()
    print(lux)
    time.sleep(1)
    