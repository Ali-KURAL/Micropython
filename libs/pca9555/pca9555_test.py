import time
from machine import I2C,Pin
from pca9555 import PCA9555

i2c = I2C(0,scl=Pin(17), sda=Pin(16))

# Assumes a PCA9555 with 16 GPIO's at address 0x20
chip = PCA9555(i2c, 0x21)
chip.set_pin(10,chip.OUT)


while True:
    chip.output(10,1)
    time.sleep(1)
    chip.output(10,0)
    time.sleep(1)