from machine import Pin, UART
from micropython import const
import math
import time,utime

TEMP = '0123456789ABCDEF*'

# Lowpower Modes
FLP_MODE = "$PQFLP,W,1,1"
GLP_MODE = "$PQGLP,W,1,1"

# CONSTANTS
PI = 3.14159265358979324
EE = 0.00669342162296594323
X_PI = 3.14159265358979324 * 3000.0 / 180.0

# Startup mode
SET_HOT_START = '$PMTK101'
SET_WARM_START = '$PMTK102'
SET_COLD_START = '$PMTK103'
SET_FULL_COLD_START = '$PMTK104'

# Standby mode -- Exit requires high level trigger
SET_PERPETUAL_STANDBY_MODE = '$PMTK161'
SET_STANDBY_MODE = '$PMTK161,0'

SET_PERIODIC_MODE = '$PMTK225'
SET_NORMAL_MODE = '$PMTK225,0'
SET_PERIODIC_BACKUP_MODE = '$PMTK225,1,1000,2000'
SET_PERIODIC_STANDBY_MODE = '$PMTK225,2,1000,2000'
SET_PERPETUAL_BACKUP_MODE = '$PMTK225,4'
SET_ALWAYSLOCATE_STANDBY_MODE = '$PMTK225,8'
SET_ALWAYSLOCATE_BACKUP_MODE = '$PMTK225,9'

# Set the message interval,100ms~10000ms
SET_POS_FIX = '$PMTK220'
SET_POS_FIX_100MS = '$PMTK220,100'
SET_POS_FIX_200MS = '$PMTK220,200'
SET_POS_FIX_400MS = '$PMTK220,400'
SET_POS_FIX_800MS = '$PMTK220,800'
SET_POS_FIX_1S = '$PMTK220,1000'
SET_POS_FIX_2S = '$PMTK220,2000'
SET_POS_FIX_4S = '$PMTK220,4000'
SET_POS_FIX_8S = '$PMTK220,8000'
SET_POS_FIX_10S = '$PMTK220,10000'

# Switching time output
SET_SYNC_PPS_NMEA_OFF = '$PMTK255,0'
SET_SYNC_PPS_NMEA_ON = '$PMTK255,1'

# To restore the system default setting
SET_REDUCTION = '$PMTK314,-1'

# Set NMEA sentence output frequencies
SET_NMEA_OUTPUT = '$PMTK314,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0'

# Baud rate
SET_NMEA_BAUDRATE = '$PMTK251'
SET_NMEA_BAUDRATE_115200 = '$PMTK251,115200'
SET_NMEA_BAUDRATE_57600 = '$PMTK251,57600'
SET_NMEA_BAUDRATE_38400 = '$PMTK251,38400'
SET_NMEA_BAUDRATE_19200 = '$PMTK251,19200'
SET_NMEA_BAUDRATE_9600 = '$PMTK251,9600'

class QL76:
    def __init__(self, port, rx, tx):
        self._port = port
        self._rx = rx
        self._tx = tx
        self._status = 0
        self.Time_Zone = 3
        self.Time_H = 0
        self.Time_M = 0
        self.Time_S = 0
        self.location_lat = 0
        self.location_long = 0
        self._serial = UART(port, 9600, tx=Pin(tx), rx=Pin(rx))
        self._L76X_Send_Command(SET_NMEA_OUTPUT)
        utime.sleep_ms(10)
        self._L76X_Send_Command(SET_SYNC_PPS_NMEA_ON)
        utime.sleep_ms(10)
        self._L76X_Send_Command(SET_POS_FIX_200MS)
        utime.sleep_ms(10)
        self._L76X_Send_Command(GLP_MODE)
        self._calibration_lat = 0
        self._calibration_long = 0

    def _L76X_Send_Command(self, data):
        Check = ord(data[1])
        for i in range(2, len(data)):
            Check = Check ^ ord(data[i])
        data = data + TEMP[16]
        data = data + TEMP[int(Check / 16)]
        data = data + TEMP[int(Check % 16)]
        data = data.encode()
        self._serial.write(data)
        self._serial.write('\r'.encode())
        self._serial.write('\n'.encode())

    def _L76X_Receive_Command(self):
        try:
            val = '--RMC'
            recv = self._serial.read(1).decode()
            val = recv
            while not val == "\n":
                val = self._serial.read(1).decode()
                recv += val
            val = '--GSV'
            while not val == "\n":
                val = self._serial.read(1).decode()
                recv += val
            return recv
        except AttributeError:
            return

    def L76X_Set_Baud(self, baud):
        if baud == 9600:
            return
        if baud == 115200:
            self._L76X_Send_Command(SET_NMEA_BAUDRATE_115200)
            time.sleep(1)
        elif baud == 57600:
            self._L76X_Send_Command(SET_NMEA_BAUDRATE_57600)
            time.sleep(1)
        elif baud == 38400:
            self._L76X_Send_Command(SET_NMEA_BAUDRATE_38400)
            time.sleep(1)
        elif baud == 19200:
            self._L76X_Send_Command(SET_NMEA_BAUDRATE_19200)
            time.sleep(1)
        elif baud == 9600:
            self._L76X_Send_Command(SET_NMEA_BAUDRATE_9600)
            time.sleep(1)
        print(baud)
        self._serial = UART(self._port, baud, tx=Pin(self._tx), rx=Pin(self._rx))
        print(self._serial)

    def _L76X_Location_Calibration(self, latitude, longitude):
        lat_long = self.L76X_GPS_Information()
        lat = lat_long[2]
        long = lat_long[3]
        self._calibration_lat = latitude - lat
        print(self._calibration_lat)
        self._calibration_long = longitude - long 
        print(self._calibration_long)

    @property
    def status(self):
        return self._status

    def L76X_GPS_Information(self):
        recv = self._L76X_Receive_Command()
        attempt = 0
        while recv is None or attempt < 10:
            recv = self._L76X_Receive_Command()
            attempt += 1
            time.sleep_ms(10)
        if recv is None:
            return
        recv = recv.split(",")
        time_val = recv[1]
        self.Time_H = str(int(time_val[:2]) + self.Time_Zone)
        self.Time_M = time_val[2:4]
        self.Time_S = time_val[4:6]
        status_val = recv[2]
        if status_val == 'V':
            return
        lat_val = list(recv[3])
        del lat_val[4]
        lat_val.insert(2, ".")
        self.location_lat = float("".join(lat_val))
        long_val = list(recv[5])
        del long_val[5]
        long_val.insert(3, ".")
        self.location_long = float("".join(long_val))
        date_val = recv[9]
        satellite = recv[14]
        return ["{}{}{}".format(self.Time_H, self.Time_M, self.Time_S), status_val,
                self.location_lat + self._calibration_lat,
                self.location_long + self._calibration_long, date_val, satellite]
