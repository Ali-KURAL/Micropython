import machine
import seesaw
import time

# Write your PINS here
scl_pin = 17
sda_pin = 16

i2c = machine.I2C(0,scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin),freq = 10000)

ss = seesaw.Seesaw(i2c)

while True:
  temp = ss.temperature
  hum = ss.moisture
  print()
  print('Temperature: ', temp)
  print('Moisture: ', hum)
  print()

  time.sleep(1)
