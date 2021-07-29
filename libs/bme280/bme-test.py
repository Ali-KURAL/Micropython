import machine
import bme280
import time

# Write your PINS here
scl_pin = 17
sda_pin = 16

i2c = machine.I2C(0,scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin),freq = 10000)

bme = bme280.BME280(i2c=i2c)
n = 0

while True:
  temp = bme.getTemperature()
  hum = bme.getHumidity()
  pres = bme.getPressure()
  # uncomment for temperature in Fahrenheit
  #temp = (bme.read_temperature()/100) * (9/5) + 32
  #temp = str(round(temp, 2)) + 'F'
  print()
  print('Temperature: ', temp)
  print('Humidity: ', hum)
  print('Pressure: ', pres)
  print()

  time.sleep(1)