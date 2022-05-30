from machine import I2C, Pin
from micropython import const

TPS63811_DEFAULT_ADDRESS = 0x75

TPS63811_CONTROL = 0x01
TPS63811_STATUS = 0x02
TPS63811_DEVID = 0x03
TPS63811_VOUT1 = 0x04
TPS63811_VOUT2 = 0x05

# CONTROL REGISTERS BITS
TPS63811_RANGE_BIT = 6
TPS63811_ENABLE_BIT = 5
TPS63811_FORCEDPWM_BIT = 3
TPS63811_RAMPPWM_BIT = 2

# Slewrate
bmSlewrate = const(0b00000011)

# Status
bfTSD = const(1)
bfPGn = const(0)

# VOUT
MIN_VRES_MV = const(25)

MIN_VOLT_HRANGE_MV = const(2025)  # Minimum voltage in H range (mV)
MAX_VOLT_HRANGE_MV = 5200  # Maximum voltage (mV) in H range
MIN_VOLT_LRANGE_MV = 1800  # Minimum voltage (mV) in L range
MAX_VOLT_LRANGE_MV = 4975  # Maximum voltage (mV) in L range

SLEWRATE_1V0_MS = const(0)
SLEWRATE_2V5_MS = const(1)
SLEWRATE_5V0_MS = const(2)
SLEWRATE_10V_MS = const(3)


class I2C_COM:
    def __init__(self, address, i2c):
        self._address = address
        self._i2c = i2c

    def regRead(self, reg: int):
        return int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 1), 'little') & 0xFF

    def regWrite(self, reg: int, value:int):
        ba = bytearray([value])
        print(ba)
        self._i2c.writeto_mem(self._address, reg, ba)


class TPS63811:
    def __init__(self, i2c_id: int, sda: int, scl: int, i2c_address=TPS63811_DEFAULT_ADDRESS):
        self._i2c = I2C_COM(i2c_address, I2C(i2c_id, scl=Pin(scl), sda=Pin(sda)))
        self._tmpStatus = 0

    @property
    def deviceID(self):
        return self._i2c.regRead(TPS63811_DEVID)

    @property
    def slewRate(self):
        return self._i2c.regRead(TPS63811_CONTROL) & bmSlewrate

    @slewRate.setter
    def slewRate(self, value: int):
        tmpRC = self._i2c.regRead(TPS63811_CONTROL)
        self._i2c.regWrite(TPS63811_CONTROL, ((tmpRC & ~bmSlewrate) | (value & bmSlewrate)))

    @property
    def rng(self):
        if self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RANGE_BIT) >> TPS63811_RANGE_BIT:
            return 1
        else:
            return 0

    @rng.setter
    def rng(self, value: int):
        tmpRC = self._i2c.regRead(TPS63811_CONTROL)
        if value is 1:
            self._i2c.regWrite(TPS63811_CONTROL,
                               (tmpRC & ~(1 << TPS63811_RANGE_BIT)) | (1 << TPS63811_RANGE_BIT))
        else:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC & ~(1 << TPS63811_RANGE_BIT)))

    @property
    def enable(self):
        return self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_ENABLE_BIT)

    @enable.setter
    def enable(self, value: bool):
        tmpRC = self._i2c.regRead(TPS63811_CONTROL)
        if value:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (1 << TPS63811_ENABLE_BIT)))
        else:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (not 1 << TPS63811_ENABLE_BIT)))

    @property
    def forced_pwm(self):
        return self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_FORCEDPWM_BIT)

    @forced_pwm.setter
    def forced_pwm(self, value: bool):
        tmpRC = self._i2c.regRead(TPS63811_CONTROL)
        if value:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (1 << TPS63811_FORCEDPWM_BIT)))
        else:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (not 1 << TPS63811_FORCEDPWM_BIT)))

    @property
    def ramp_pwm(self):
        return self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RAMPPWM_BIT)

    @ramp_pwm.setter
    def ramp_pwm(self, value: bool):
        tmpRC = self._i2c.regRead(TPS63811_CONTROL)
        if value:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (1 << TPS63811_RAMPPWM_BIT)))
        else:
            self._i2c.regWrite(TPS63811_CONTROL, (tmpRC | (not 1 << TPS63811_RAMPPWM_BIT)))

    @property
    def power_good(self):
        self._tmpStatus |= self._i2c.regRead(TPS63811_STATUS)
        print(self._tmpStatus)
        print(self._tmpStatus)
        tmpEFlag = self._tmpStatus
        self._tmpStatus &= (not (1 << bfPGn))
        return not (tmpEFlag & (1 << bfPGn))

    @property
    def thermal_good(self):
        self._tmpStatus |= self._i2c.regRead(TPS63811_STATUS)
        tmpEFlag = self._tmpStatus
        self._tmpStatus &= (not (1 << bfTSD))
        return not (tmpEFlag & (1 << bfTSD))

    @property
    def out_1(self):
        if self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RANGE_BIT):
            mv_min = MIN_VOLT_HRANGE_MV
        else:
            mv_min = MIN_VOLT_LRANGE_MV

        mv_cur = self._i2c.regRead(TPS63811_VOUT1)

        return (mv_cur * MIN_VRES_MV + mv_min)/1000

    @property
    def out_2(self):
        if self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RANGE_BIT):
            mv_min = MIN_VOLT_HRANGE_MV
        else:
            mv_min = MIN_VOLT_LRANGE_MV

        mv_cur = self._i2c.regRead(TPS63811_VOUT2)

        return (mv_cur * MIN_VRES_MV + mv_min)/1000

    @out_1.setter
    def out_1(self, value: int):
        mv_set = value
        if self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RANGE_BIT):
            mv_max = MAX_VOLT_HRANGE_MV
            mv_min = MIN_VOLT_HRANGE_MV
        else:
            mv_max = MAX_VOLT_LRANGE_MV
            mv_min = MIN_VOLT_LRANGE_MV

        if mv_set < mv_min:
            mv_set = mv_min
        if mv_set > mv_max:
            mv_set = mv_max

        self._i2c.regWrite(TPS63811_VOUT1, int(((mv_set - mv_min) / MIN_VRES_MV)))

    @out_2.setter
    def out_2(self, value: int): 
        mv_set = value
        if self._i2c.regRead(TPS63811_CONTROL) & (1 << TPS63811_RANGE_BIT):
            mv_max = MAX_VOLT_HRANGE_MV
            mv_min = MIN_VOLT_HRANGE_MV
        else:
            mv_max = MAX_VOLT_LRANGE_MV
            mv_min = MIN_VOLT_LRANGE_MV

        if mv_set < mv_min:
            mv_set = mv_min
        if mv_set > mv_max:
            mv_set = mv_max

        self._i2c.regWrite(TPS63811_VOUT2, int(((mv_set - mv_min) / MIN_VRES_MV)))
