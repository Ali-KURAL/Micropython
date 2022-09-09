import time

from ads1115 import ADS1115
ads1115 = ADS1115(0,17,16)

while True :
	adc = ads1115.read_adc_single_ended(0)
	print("Digital Value of Analog Input : %d " % (adc))
	print(" ********************************************* ")
    	time.sleep(1)
