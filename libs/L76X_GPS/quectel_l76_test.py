from Quectel_L76_GPS import QL76
import time


quec = QL76(port = 0,rx = 1,tx = 0)

quec.L76X_Set_Baud(115200)

your_lat = 0 # fixed location
your_long =  0 # fixed location
quec._L76X_Location_Calibration(your_lat, your_long)

while True:
    print(quec.L76X_GPS_Information())
    time.sleep(0.5)
