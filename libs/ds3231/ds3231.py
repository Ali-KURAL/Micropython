from machine import I2C, Pin
from math import floor
from micropython import const
import time

DS3231_I2C_ADDRESS = const(0x68)


def decodeToDec(byte):
    return ((byte >> 4) * 10) + (byte & 0x0F)


def encodeToByte(dec):
    tens = floor(dec / 10)
    ones = dec - tens * 10
    return (tens << 4) + ones


class I2C_COM:
    def __init__(self, address, i2c):
        self._address = address
        self._i2c = i2c

    def regRead(self, reg: int):
        return int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 1), 'little') & 0xFF

    def regWrite(self, reg: int, value):
        ba = bytearray([value])
        self._i2c.writeto_mem(self._address, reg, ba)


class DS3231:
    def __init__(self, i2c_id: int, scl: int, sda: int, i2c_address: int = DS3231_I2C_ADDRESS):
        # create RTC instance with I2C Pins
        self._i2c = I2C_COM(i2c_address, I2C(i2c_id, scl=Pin(scl), sda=Pin(sda)))
        self._tmpStatus = 0
        self._timezone = 3

    # get times functions
    # -------------------------------------------------------------------------------------------------------

    def getYear(self):
        return decodeToDec(self._i2c.regRead(0x06))

    def getMonth(self):
        temp = self._i2c.regRead(0x05)
        return decodeToDec(temp)

    def getDay(self):
        return decodeToDec(self._i2c.regRead(0x04))

    def getDayOfWeek(self):
        return decodeToDec(self._i2c.regRead(0x03))

    def getHour(self):
        temp = self._i2c.regRead(0x02)
        return decodeToDec(temp & 0x3F)

    def getMinutes(self):
        return decodeToDec(self._i2c.regRead(0x01))

    def getSeconds(self):
        return decodeToDec(self._i2c.regRead(0x00))

    def getDateTime(self):
        # returns whole date and time as list
        # (last two digits of year, month, day, day of week, hour, minutes, seconds)
        dateTime = [0, 0, 0, 0, 0, 0, 0]
        dateTime[0] = self.getYear()
        dateTime[1] = self.getMonth()
        dateTime[2] = self.getDay()
        dateTime[3] = self.getDayOfWeek()
        dateTime[4] = self.getHour()
        dateTime[5] = self.getMinutes()
        dateTime[6] = self.getSeconds()
        return dateTime

    def setYear(self, year):
        # only last two digits (last two digits are used if longer)
        if year > 99:
            thousands = floor(year / 100)
            year = year - (thousands * 100)
        self._i2c.regWrite(0x06, encodeToByte(year))

    def setMonth(self, month):
        self._i2c.regWrite(0x05, encodeToByte(month) | 0)

    def setDay(self, day):
        self._i2c.regWrite(0x04, encodeToByte(day))

    def setDayOfWeek(self, dayOfWeek):
        self._i2c.regWrite(0x03, encodeToByte(dayOfWeek))

    def setHour(self, hour):
        self._i2c.regWrite(0x02, encodeToByte(hour) & 0x3F)

    def setMinutes(self, minutes):
        self._i2c.regWrite(0x01, encodeToByte(minutes))

    def setSeconds(self, seconds):
        self._i2c.regWrite(0x00, encodeToByte(seconds))

    def setDateTime(self, year, month, day, dayOfWeek, hour, minutes, seconds):
        # set all the date and times (year is last two digits of year)
        self.setYear(year)
        self.setMonth(month)
        self.setDay(day)
        self.setDayOfWeek(dayOfWeek)
        self.setHour(hour)
        self.setMinutes(minutes)
        self.setSeconds(seconds)

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, val):
        self._timezone = val

    @property
    def unix(self):

        dateTime = [0, 0, 0, 0, 0, 0, 0]
        dateTime[0] = int(self.getYear())
        dateTime[1] = int(self.getMonth())
        dateTime[2] = int(self.getDay())
        dateTime[3] = int(self.getDayOfWeek())
        dateTime[4] = int(self.getHour())
        dateTime[5] = int(self.getMinutes())
        dateTime[6] = int(self.getSeconds())
        current_year = dateTime[0]
        if current_year % 4 == 0:
            additional = 1
        else:
            additional = 0

        current_month = dateTime[1]
        unix_day = 31 + (28 + additional) - 1
        for m in range(3, current_month):
            if m % 2 != 0:
                unix_day += 31
            else:
                unix_day += 30
        unix_day = dateTime[2] + unix_day

        unix = time.mktime((dateTime[0] + 2000, dateTime[1], dateTime[2], dateTime[4], dateTime[5], dateTime[6],
                            dateTime[3], unix_day, -1)) - (self._timezone * 3600)
        return unix

    #
    #         unix_day += current_day - 1
    #         unix_day = unix_day * UNIX_DAY
    #         unix_hour = self.getHour() * UNIX_HOUR
    #         unix_min = self.getMinutes() * 60
    #         unix_sec = self.getSeconds()
    #         print(unix_year + unix_day )
    #         return unix_year + unix_day + unix_hour + unix_min + unix_sec

    def getAlarm1(self):
        # returns list as:
        # dayOfWeek or day (depending on setup in setAlarm), hour, minutes, seconds, type of alarm
        alarmTime = [0, 0, 0, 0, ""]
        alarmTime[0] = self._i2c.regRead(0x0A)
        alarmTime[1] = self._i2c.regRead(0x09)
        alarmTime[2] = self._i2c.regRead(0x08)
        alarmTime[3] = self._i2c.regRead(0x07)
        alarmTime[4] = decodeAlarmType(alarmTime)
        alarmTime = decodeAlarmTime(alarmTime)
        return alarmTime

    def getAlarm2(self):
        # returns list as:
        # dayOfWeek or day (depending on setup in setAlarm), hour, minutes, type of alarm
        alarmTime = [0, 0, 0, ""]
        alarmTime[0] = self._i2c.regRead(0x0D)
        alarmTime[1] = self._i2c.regRead(0x0C)
        alarmTime[2] = self._i2c.regRead(0x0B)
        alarmTime[3] = decodeAlarmType(alarmTime)
        alarmTime = decodeAlarmTime(alarmTime)
        return alarmTime

    def alarmTriggered(self, alarmNumber):
        # check if alarm triggert and reset alarm flag
        statusBits = self._i2c.regRead(0x0F)
        if statusBits & alarmNumber:
            self.resetAlarm(alarmNumber)
            return True
        else:
            return False

    def setAlarm1(self, day, hour, minutes, seconds=0, alarmType="everyDay"):
        # alarm Types are:
        #    "everySecond"  - alarm every second
        #    "everyMinute"  - alarm when seconds match
        #    "everyHour"    - alarm when minutes and seconds match
        #    "everyDay"     - alarm when hours, minutes and seconds match ! default !
        #    "everyWeek"    - alarm when day of week, hours, minutes and seconds match
        #    "everyMonth"   - alarm when day of month, hours, minutes and seconds match

        alarmTime = encodeDateTime(day, hour, minutes, seconds, alarmType)
        self._i2c.regWrite(0x07, alarmTime[3])
        self._i2c.regWrite(0x08, alarmTime[2])
        self._i2c.regWrite(0x09, alarmTime[1])
        self._i2c.regWrite(0x0A, alarmTime[0])

    def setAlarm2(self, day, hour, minutes, alarmType="everyDay"):
        # alarm Types are:
        #    "everyMinute"  - alarm every minute (at 00 seconds)
        #    "everyHour"    - alarm when minutes match
        #    "everyDay"     - alarm when hours and minutes match ! default !
        #    "everyWeek"    - alarm when day of week, hours and minutes match
        #    "everyMonth"   - alarm when day of month, hours and minutes match
        seconds = 0
        alarmTime = encodeDateTime(day, hour, minutes, seconds, alarmType)
        self._i2c.regWrite(0x0B, alarmTime[2])
        self._i2c.regWrite(0x0C, alarmTime[1])
        self._i2c.regWrite(0x0D, alarmTime[0])

    def turnOnAlarmIR(self, alarmNumber):
        # set alarm interrupt. AlarmNumber 1 or 2
        # when turned on, interrupt pin on DS3231 is "False" when alarm has been triggert
        controlRegister = self._i2c.regRead(0x0E)
        setByte = 0x04
        setByte = setByte + alarmNumber
        setByte = controlRegister | setByte
        self._i2c.regWrite(0x0E, setByte)

    def turnOffAlarmIR(self, alarmNumber):
        # turn off alarm interrupt. Alarmnumber 1 or 2
        # only initiation of interrupt is turned off,
        # alarm flag is still set when alarm conditions meet (i don't get it either)
        controlRegister = self._i2c.regRead(0x0E)
        setByte = 0xFF
        setByte = setByte - alarmNumber
        setByte = controlRegister & setByte
        self._i2c.regWrite(0x0E, setByte)

    def resetAlarmFlag(self, alarmNumber):
        statusBits = self._i2c.regRead(0x0F)
        self._i2c.regWrite(0x0F, statusBits & (0xFF - alarmNumber))

    def resetAlarm(self, alarmNumber):
        pass


def decodeAlarmType(alarmTime):
    if len(alarmTime) > 4:
        m1Bit = (alarmTime[3] & 0x80) >> 7
    else:
        m1Bit = False
    m2Bit = (alarmTime[2] & 0x80) >> 7
    m3Bit = (alarmTime[1] & 0x80) >> 7
    m4Bit = (alarmTime[0] & 0x80) >> 7
    dayBit = (alarmTime[0] & 0x40) >> 6

    if m1Bit and m2Bit and m3Bit and m4Bit:
        return "everySecond"
    elif not m1Bit and m2Bit and m3Bit and m4Bit:
        return "everyMinute"
    elif not m1Bit and not m2Bit and m3Bit and m4Bit:
        return "everyHour"
    elif not m1Bit and not m2Bit and not m3Bit and m4Bit:
        return "everyDay"
    elif not dayBit and not m1Bit and not m2Bit and not m3Bit and not m4Bit:
        return "everyMonth"
    elif dayBit and not m1Bit and not m2Bit and not m3Bit and not m4Bit:
        return "everyWeek"
    else:
        return "noValidAlarmType"


def decodeAlarmTime(alarmTime):
    alarmTime[0] = decodeToDec(alarmTime[0] & 0x3F)
    alarmTime[1] = decodeToDec(alarmTime[1] & 0x3F)
    alarmTime[2] = decodeToDec(alarmTime[2] & 0x7F)
    if len(alarmTime) > 4:
        alarmTime[3] = decodeToDec(alarmTime[3] & 0x7F)
    return alarmTime


def encodeAlarmType(alarmType):
    if alarmType == "everySecond":
        return 15  # 0b01111
    elif alarmType == "everyMinute":
        return 14  # 0b01110
    elif alarmType == "everyHour":
        return 12  # 0b01100
    elif alarmType == "everyDay":
        return 8  # 0b01000
    elif alarmType == "everyMonth":
        return 0  # 0b00000
    elif alarmType == "everyWeek":
        return 16  # 0b10000
    else:
        raise ValueError("""Not a supported alarmType. Options are: 
        'everySecond' (only Alarm 1), 'everyMinute', 'everyHour', 'everyDay', 'everyMonth', 'everyWeek'""")


def encodeDateTime(day, hour, minutes, seconds, alarmType):
    alarmBits = encodeAlarmType(alarmType)
    alarmTime = [0, 0, 0, 0]
    alarmTime[0] = (encodeToByte(day) & 0x3F) | ((alarmBits & 0x10) << 2) | ((alarmBits & 0x08) << 4)
    alarmTime[1] = (encodeToByte(hour) & 0x3F) | ((alarmBits & 0x04) << 5)
    alarmTime[2] = (encodeToByte(minutes) & 0x7F) | ((alarmBits & 0x02) << 6)
    alarmTime[3] = (encodeToByte(seconds) & 0x7F) | ((alarmBits & 0x01) << 7)
    return alarmTime

