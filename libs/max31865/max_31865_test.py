import time
from max_31865_1shot import MAX31865

mx = MAX31865(1, mosi=11, miso=12, sck=10, cs=13)

time.sleep(0.25)
while True:
    temp = mx.temperature
    print("Temperatur: ", temp)
    time.sleep(0.2)
