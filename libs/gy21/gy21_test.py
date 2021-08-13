import machine
import gy21
import time

# Write your PINS here
scl_pin = 17
sda_pin = 16

i2c = machine.I2C(0,scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin),freq = 10000)

gy = gy21.GY21(i2c)

while True:
  temp = gy.temperature
  hum = gy.humidity
  print()
  print('Temperature: ', temp)
  print('Humidity: ', hum)
  print()

  time.sleep(1)