import math,time

from micropython import const
from machine import SPI, Pin

# STEP_MODE option values.
STEP_MODE_STEP_SEL = const(0x07)

STEP_SEL_1 = const(0x00)
STEP_SEL_1_2 = const(0x01)
STEP_SEL_1_4 = const(0x02)
STEP_SEL_1_8 = const(0x03)
STEP_SEL_1_16 = const(0x04)
STEP_SEL_1_32 = const(0x05)
STEP_SEL_1_64 = const(0x06)
STEP_SEL_1_128 = const(0x07)

STEP_MODE_SYNC_EN = const(0x80)
SYNC_EN = const(0x80)

STEP_MODE_SYNC_SEL = const(0x70)
SYNC_SEL_1_2 = const(0x00)
SYNC_SEL_1 = const(0x10)
SYNC_SEL_2 = const(0x20)
SYNC_SEL_4 = const(0x30)
SYNC_SEL_8 = const(0x40)
SYNC_SEL_16 = const(0x50)
SYNC_SEL_32 = const(0x60)
SYNC_SEL_64 = const(0x70)

STEP_MODE_CM_VM = const(0x08)
VOLTAGE_MODE = const(0x00)
CURRENT_MODE = const(0x01)

ALARM_EN_OVERCURRENT = const(0x01)
ALARM_EN_THERMAL_SHUTDOWN = const(0x02)
ALARM_EN_THERMAL_WARNING = const(0x04)
ALARM_EN_UNDER_VOLTAGE = const(0x08)
ALARM_EN_ADC_UVLO = const(0x10)
ALARM_EN_STALL_DETECT = const(0x20)
ALARM_EN_SW_TURN_ON = const(0x40)
ALARM_EN_CMD_ERROR = const(0x80)

CONFIG_OSC_SEL = const(0x000F)
CONFIG_INT_16MHZ = const(0x0000)
CONFIG_INT_16MHZ_OSCOUT_2MHZ = const(0x0008)
CONFIG_INT_16MHZ_OSCOUT_4MHZ = const(0x0009)
CONFIG_INT_16MHZ_OSCOUT_8MHZ = const(0x000A)
CONFIG_INT_16MHZ_OSCOUT_16MHZ = const(0x000B)
CONFIG_EXT_8MHZ_XTAL_DRIVE = const(0x0004)
CONFIG_EXT_16MHZ_XTAL_DRIVE = const(0x0005)
CONFIG_EXT_24MHZ_XTAL_DRIVE = const(0x0006)
CONFIG_EXT_32MHZ_XTAL_DRIVE = const(0x0007)
CONFIG_EXT_8MHZ_OSCOUT_INVERT = const(0x000C)
CONFIG_EXT_16MHZ_OSCOUT_INVERT = const(0x000D)
CONFIG_EXT_24MHZ_OSCOUT_INVERT = const(0x000E)
CONFIG_EXT_32MHZ_OSCOUT_INVERT = const(0x000F)

CONFIG_SW_MODE = const(0x0010)
CONFIG_SW_HARD_STOP = const(0x0000)
CONFIG_SW_USER = const(0x0010)

CONFIG_EN_VSCOMP = const(0x0020)
CONFIG_VS_COMP_DISABLE = const(0x0000)
CONFIG_VS_COMP_ENABLE = const(0x0020)

CONFIG_OC_SD = const(0x0080)
CONFIG_OC_SD_DISABLE = const(0x0000)
CONFIG_OC_SD_ENABLE = const(0x0080)

CONFIG_UVLOVAL = const(0x0100)
CONFIG_UVLOVAL_LOW = const(0x0000)
CONFIG_UVLOVAL_HIGH = const(0x0100)

CONFIG_VCCVAL = const(0x0200)
CONFIG_VCCVAL_7_5V = const(0x0000)
CONFIG_VCCVAL_15V = const(0x0200)

CONFIG_F_PWM_DEC = const(0x1C00)
CONFIG_PWM_MUL_0_625 = const(0x00 << 10)
CONFIG_PWM_MUL_0_75 = const(0x01 << 10)
CONFIG_PWM_MUL_0_875 = const(0x02 << 10)
CONFIG_PWM_MUL_1 = const(0x03 << 10)
CONFIG_PWM_MUL_1_25 = const(0x04 << 10)
CONFIG_PWM_MUL_1_5 = const(0x05 << 10)
CONFIG_PWM_MUL_1_75 = const(0x06 << 10)
CONFIG_PWM_MUL_2 = const(0x07 << 10)

CONFIG_F_PWM_INT = const(0xE000)
CONFIG_PWM_DIV_1 = const(0x00 << 13)
CONFIG_PWM_DIV_2 = const(0x01 << 13)
CONFIG_PWM_DIV_3 = const(0x02 << 13)
CONFIG_PWM_DIV_4 = const(0x03 << 13)
CONFIG_PWM_DIV_5 = const(0x04 << 13)
CONFIG_PWM_DIV_6 = const(0x05 << 13)
CONFIG_PWM_DIV_7 = const(0x06 << 13)

CONFIG_PRED = const(0x8000)
CONFIG_PRED_DISABLE = const(0x0000)
CONFIG_PRED_ENABLE = const(0x8000)

CONFIG_TSW = const(0x7C00)

STATUS_HIZ = const(0x0001)
STATUS_BUSY = const(0x0002)
STATUS_SW_F = const(0x0004)
STATUS_SW_EVN = const(0x0008)

STATUS_DIR = const(0x0010)

STATUS_CMD_ERROR = const(0x0080)
STATUS_STCK_MOD = const(0x0100)
STATUS_UVLO = const(0x0200)
STATUS_UVLO_ADC = const(0x0400)

STATUS_OCD = const(0x2000)
STATUS_STALL_B = const(0x4000)
STATUS_STALL_A = const(0x8000)

# Status register thermal status field
STATUS_TH_STATUS = const(0x1800)
STATUS_TH_NORMAL = const(0x0000 << 11)
STATUS_TH_WARNING = const(0x0001 << 11)
STATUS_TH_BRIDGE_SHUTDOWN = const(0x0002 << 11)
STATUS_TH_DEVICE_SHUTDOWN = const(0x0003 << 11)

# Status register motor status field
STATUS_MOT_STATUS = const(0x0060)
STATUS_MOT_STATUS_STOPPED = const(0x0000 << 5)
STATUS_MOT_STATUS_ACCELERATION = const(0x0001 << 5)
STATUS_MOT_STATUS_DECELERATION = const(0x0002 << 5)
STATUS_MOT_STATUS_CONST_SPD = const(0x0003 << 5)

# Register address redefines.
# See the Param_Handler() function for more info about these.
ABS_POS = const(0x01)
EL_POS = const(0x02)
MARK = const(0x03)
SPEED = const(0x04)
ACC = const(0x05)
DECEL = const(0x06)
MAX_SPEED = const(0x07)
MIN_SPEED = const(0x08)
FS_SPD = const(0x15)
KVAL_HOLD = const(0x09)
KVAL_RUN = const(0x0A)
KVAL_ACC = const(0x0B)
KVAL_DEC = const(0x0C)
INT_SPD = const(0x0D)
ST_SLP = const(0x0E)
FN_SLP_ACC = const(0x0F)
FN_SLP_DEC = const(0x10)
K_THERM = const(0x11)
ADC_OUT = const(0x12)
OCD_TH = const(0x13)
STALL_TH = const(0x14)
STEP_MODE = const(0x16)
ALARM_EN = const(0x17)
GATECFG1 = const(0x18)
GATECFG2 = const(0x19)
CONFIG = const(0x1A)
STATUS = const(0x1B)

# Current mode configuration
TVAL_HOLD = const(0x09)
TVAL_RUN = const(0x0A)
TVAL_ACC = const(0x0B)
TVAL_DEC = const(0x0C)
T_FAST = const(0x0E)
TON_MIN = const(0x0F)
TOFF_MIN = const(0x10)

# dSPIN commands
NOP = const(0x00)
SET_PARAM = const(0x00)
GET_PARAM = const(0x20)
RUN = const(0x50)
STEP_CLOCK = const(0x58)
MOVE = const(0x40)
GOTO = const(0x60)
GOTO_DIR = const(0x68)
GO_UNTIL = const(0x82)
RELEASE_SW = const(0x92)
GO_HOME = const(0x70)
GO_MARK = const(0x78)
RESET_POS = const(0xD8)
RESET_DEVICE = const(0xC0)
SOFT_STOP = const(0xB0)
HARD_STOP = const(0xB8)
SOFT_HIZ = const(0xA0)
HARD_HIZ = const(0xA8)
GET_STATUS = const(0xD0)

# dSPIN direction
FWD = const(0x01)
REV = const(0x00)

RESET_ABSPOS = const(0x00)
COPY_ABSPOS = const(0x08)

BUSY_PIN = const(0x00)
SYNC_PIN = const(0x80)

# divisors for SYNC pulse outputs
SYNC_FS_2 = const(0x00)
SYNC_FS = const(0x10)
SYNC_2FS = const(0x20)
SYNC_4FS = const(0x30)
SYNC_8FS = const(0x40)
SYNC_16FS = const(0x50)
SYNC_32FS = const(0x60)
SYNC_64FS = const(0x70)

# configStepMode() options
STEP_FS = const(0x00)
STEP_FS_2 = const(0x01)
STEP_FS_4 = const(0x02)
STEP_FS_8 = const(0x03)
STEP_FS_16 = const(0x04)
STEP_FS_32 = const(0x05)
STEP_FS_64 = const(0x06)
STEP_FS_128 = const(0x07)

# PWM Multiplier and divisor options
PWM_MUL_0_625 = const(0x00 << 10)
PWM_MUL_0_75 = const(0x01 << 10)
PWM_MUL_0_875 = const(0x02 << 10)
PWM_MUL_1 = const(0x03 << 10)
PWM_MUL_1_25 = const(0x04 << 10)
PWM_MUL_1_5 = const(0x05 << 10)
PWM_MUL_1_75 = const(0x06 << 10)
PWM_MUL_2 = const(0x07 << 10)
PWM_DIV_1 = const(0x00 << 13)
PWM_DIV_2 = const(0x01 << 13)
PWM_DIV_3 = const(0x02 << 13)
PWM_DIV_4 = const(0x03 << 13)
PWM_DIV_5 = const(0x04 << 13)
PWM_DIV_6 = const(0x05 << 13)
PWM_DIV_7 = const(0x06 << 13)

# Slew rate options
SR_114V_us = const(0x0040 | 0x0018)
SR_220V_us = const(0x0060 | 0x000C)
SR_400V_us = const(0x0080 | 0x0007)
SR_520V_us = const(0x00A0 | 0x0006)
SR_790V_us = const(0x00C0 | 0x0003)
SR_980V_us = const(0x00D0 | 0x0002)

# Over-current bridge shutdown options
OC_SD_DISABLE = const(0x0000)
OC_SD_ENABLE = const(0x0080)

# Voltage compensation settings
VS_COMP_DISABLE = const(0x0000)
VS_COMP_ENABLE = const(0x0020)

# External switch input functionality.
SW_HARD_STOP = const(0x0000)
SW_USER = const(0x0010)

# Clock functionality
INT_16MHZ = const(0x0000)
INT_16MHZ_OSCOUT_2MHZ = const(0x0008)
INT_16MHZ_OSCOUT_4MHZ = const(0x0009)
INT_16MHZ_OSCOUT_8MHZ = const(0x000A)
INT_16MHZ_OSCOUT_16MHZ = const(0x000B)
EXT_8MHZ_XTAL_DRIVE = const(0x0004)
EXT_16MHZ_XTAL_DRIVE = const(0x0005)
EXT_24MHZ_XTAL_DRIVE = const(0x0006)
EXT_32MHZ_XTAL_DRIVE = const(0x0007)
EXT_8MHZ_OSCOUT_INVERT = const(0x000C)
EXT_16MHZ_OSCOUT_INVERT = const(0x000D)
EXT_24MHZ_OSCOUT_INVERT = const(0x000E)
EXT_32MHZ_OSCOUT_INVERT = const(0x000F)

NUMBER_OF_BOARDS = 0


def accCalc(stepsPerSecPerSec):
    temp = stepsPerSecPerSec * 0.137438
    if temp > 0x00000FFF:
        return 0x00000FFF
    else:
        return temp


def accParse(stepsPerSecPerSec):
    return float(stepsPerSecPerSec & 0x00000FFF) / 0.137438


def decCalc(stepsPerSecPerSec):
    temp = stepsPerSecPerSec * 0.137438
    if temp > 0x00000FFF:
        return 0x00000FFF
    else:
        return temp


def decParse(stepsPerSecPerSec):
    return float(stepsPerSecPerSec & 0x00000FFF) / 0.137438


def maxSpdCalc(stepsPerSec):
    temp = math.ceil(stepsPerSec * .065536)
    if temp > 0x000003FF:
        return 0x000003FF
    else:
        return temp


def maxSpdParse(stepsPerSec):
    return float(stepsPerSec & 0x000003FF) / 0.065536


def minSpdCalc(stepsPerSec):
    temp = stepsPerSec / 0.238
    if temp > 0x00000FFF:
        return 0x00000FFF
    else:
        return temp


def minSpdParse(stepsPerSec):
    return float((stepsPerSec & 0x00000FFF) * 0.238)


def FSCalc(stepsPerSec):
    return ((float(stepsPerSec & 0x000003FF)) + 0.5) / 0.065536


def FSParse(stepsPerSec):
    return ((float(stepsPerSec & 0x000003FF)) + 0.5) / 0.065536


def intSpdCalc(stepsPerSec):
    temp = stepsPerSec * 4.1943
    if temp > 0x00003FFF:
        return 0x00003FFF
    else:
        return temp


def intSpdParse(stepsPerSec):
    return float(stepsPerSec & 0x00003FFF) / 4.1943


def spdCalc(stepsPerSec):
    temp = stepsPerSec * 67.106
    if temp > 0x000FFFFF:
        return 0x000FFFFF
    else:
        return temp


def spdParse(stepsPerSec):
    return float(stepsPerSec & 0x000FFFFF) / 67.106


class SPI_COM:
    def __init__(self, spi_id, cs, sck, mosi, miso, _numBoards, _position):
        self._spi = SPI(spi_id,
                        baudrate=2000000,
                        polarity=0,
                        phase=1,
                        bits=8,
                        firstbit=SPI.MSB,
                        sck=Pin(sck),
                        mosi=Pin(mosi),
                        miso=Pin(miso))
        print(self._spi)
        self._numBoards = _numBoards
        self._position = _position
        self._cs = Pin(cs, Pin.OUT)
        self._cs.value(1)
        time.sleep(0.1)

    def xferParam(self, value, bit_len):
        byteLen = bit_len // 8  # calculate bytes

        if bit_len % 8 > 0:
            byteLen += 1  # Make sure not to lose any partial byte values.
        retVal = 0
        for i in range(byteLen):
            retVal = retVal << 8
            temp = self.SPIXfer(value >> ((byteLen - i - 1) * 8))
            retVal |= temp

        mask = 0xffffffff >> (32 - bit_len)
        return retVal & mask

    def SPIXfer(self, data):
        self._cs.value(0)
        rx = bytearray(1)
        self._spi.write_readinto(data.to_bytes(1,"big"),rx)
        self._cs.value(1)
        return rx
    
    def set_param(self, param, value):
        param |= SET_PARAM
        self.SPIXfer(param)
        self.param_handler(param, value)

    def get_param(self, param):
        self.SPIXfer(param | GET_PARAM)
        return self.param_handler(param, 0)

    def param_handler(self, param, value):
        if param == ABS_POS:
            return self.xferParam(value, 22)
        elif param == EL_POS:
            return self.xferParam(value, 9)
        elif param == MARK:
            return self.xferParam(value, 22)
        elif param == SPEED:
            return self.xferParam(value, 20)
        elif param == ACC:
            return self.xferParam(value, 12)
        elif param == DECEL:
            return self.xferParam(value, 12)
        elif param == MAX_SPEED:
            return self.xferParam(value, 10)
        elif param == MIN_SPEED:
            return self.xferParam(value, 13)
        elif param == FS_SPD:
            return self.xferParam(value, 10)
        elif param == KVAL_HOLD:
            return self.xferParam(value, 8)
        elif param == KVAL_RUN:
            return self.xferParam(value, 8)
        elif param == KVAL_ACC:
            return self.xferParam(value, 8)
        elif param == KVAL_DEC:
            return self.xferParam(value, 8)
        elif param == INT_SPD:
            return self.xferParam(value, 14)
        elif param == ST_SLP:
            return self.xferParam(value, 8)
        elif param == FN_SLP_ACC:
            return self.xferParam(value, 8)
        elif param == FN_SLP_DEC:
            return self.xferParam(value, 8)
        elif param == K_THERM:
            value = value & 0x0F
            return self.xferParam(value, 8)
        elif param == ADC_OUT:
            return self.xferParam(value, 8)
        elif param == OCD_TH:
            value = value & 0x1F
            return self.xferParam(value, 8)
        elif param == STALL_TH:
            value = value & 0x1F
            return self.xferParam(value, 8)
        elif param == STEP_MODE:
            return self.xferParam(value, 8)
        elif param == ALARM_EN:
            return self.xferParam(value, 8)
        elif param == GATECFG1:
            return self.xferParam(value, 16)
        elif param == GATECFG2:
            return self.xferParam(value, 8)
        elif param == CONFIG:
            return self.xferParam(value, 16)
        elif param == STATUS:
            return self.xferParam(value, 16)
        else:
            self.SPIXfer(value)


class PS01_CONFIG:
    def __init__(self):
        self.syncPinMode = None
        self.syncDivisor = None
        self.stepMode = None
        self.maxSpeed = None
        self.minSpeed = None
        self.fullStepsSpeed = None
        self.acceleration = None
        self.deceleration = None
        self.slewRate = None
        self.overCurrentThreshold = None
        self.overCurrentShutdown = None
        self.pwmDivisor = None
        self.pwmMultiplier = None
        self.voltageCompensation = None
        self.switchMode = None
        self.clockSource = None
        self.runKval = None
        self.accelerationKval = None
        self.decelerationKval = None
        self.holdKval = None
        self.alarmEn = None

    def fullReset(self):
        self.syncPinMode = BUSY_PIN
        self.syncDivisor = 0

        self.stepMode = STEP_FS_128

        self.maxSpeed = 500
        self.minSpeed = 0
        self.fullStepsSpeed = 500
        self.acceleration = 1000
        self.deceleration = 1000

        self.slewRate = SR_520V_us

        self.overCurrentThreshold = 20
        self.overCurrentShutdown = OC_SD_DISABLE

        self.pwmDivisor = PWM_DIV_1
        self.pwmMultiplier = PWM_MUL_1

        self.voltageCompensation = VS_COMP_DISABLE

        self.switchMode = SW_HARD_STOP

        self.clockSource = INT_16MHZ

        self.runKval = 64
        self.accelerationKval = 64
        self.decelerationKval = 64
        self.holdKval = 32

        self.alarmEn = 0xEF

    def basicReset(self):
        self.maxSpeed = 500
        self.overCurrentThreshold = 20
        self.runKval = 64
        self.holdKval = 32


class POWERSTEP01:
    def __init__(self, spi_id, cs, sck, mosi, miso, reset_pin, position, busy_pin=-1):
        global NUMBER_OF_BOARDS
        NUMBER_OF_BOARDS += 1
        self._spi = SPI_COM(spi_id=spi_id, cs=cs, sck=sck, mosi=mosi, miso=miso, _position=position,
                            _numBoards=NUMBER_OF_BOARDS)
        self._reset = Pin(reset_pin, Pin.OUT)
        self._reset.value(1)
        self._busy_pin = busy_pin
        if not busy_pin == -1:
            self._busy = Pin(busy_pin, Pin.IN)
        self._reset.value(0)

    def busyCheck(self):
        if self._busy_pin == -1:
            if self._spi.get_param(STATUS) & 0x0002:
                return 0
            else:
                return 1
        else:
            if self._busy() == 1:
                return 0
            else:
                return 1

    def configSyncPin(self, pinFunc, syncSteps):
        syncPinConfig = self._spi.get_param(STEP_MODE)
        syncPinConfig &= 0x0F
        syncPinConfig |= ((pinFunc & 0x80) | (syncSteps & 0x70))
        self._spi.set_param(STEP_MODE, syncPinConfig)

    def configStepMode(self, stepMode):
        stepModeConfig = self._spi.get_param(STEP_MODE)
        stepModeConfig &= 0xF8
        stepModeConfig |= (stepMode & 0x07)
        self._spi.set_param(STEP_MODE, stepModeConfig)

    def getStepMode(self):
        return self._spi.get_param(STEP_MODE) & 0x07

    def setMaxSpeed(self, stepsPerSecond):
        integerSpeed = int(maxSpdCalc(stepsPerSecond))
        self._spi.set_param(MAX_SPEED, integerSpeed)

    def getMaxSpeed(self):
        return maxSpdParse(self._spi.get_param(MAX_SPEED))

    def setMinSpeed(self, stepsPerSecond):
        integerSpeed = int(minSpdCalc(stepsPerSecond))

        temp = self._spi.get_param(MIN_SPEED) & 0x00001000

        self._spi.set_param(MIN_SPEED, integerSpeed | temp)

    def getMinSpeed(self):
        return minSpdParse(self._spi.get_param(MIN_SPEED))

    def setFullSpeed(self, stepsPerSecond):
        integerSpeed = int(FSCalc(stepsPerSecond))
        self._spi.set_param(FS_SPD, integerSpeed)

    def getFullSpeed(self):
        return FSParse(self._spi.get_param(FS_SPD))

    def setAcc(self, stepsPerSecondPerSecond):
        integerAcc = int(accCalc(stepsPerSecondPerSecond))
        self._spi.set_param(ACC, integerAcc)

    def getAcc(self):
        return accParse(self._spi.get_param(ACC))

    def setDec(self, stepsPerSecondPerSecond):
        integerDec = int(decCalc(stepsPerSecondPerSecond))
        self._spi.set_param(DECEL, integerDec)

    def getDec(self):
        return accParse(self._spi.get_param(DECEL))

    def setOCThreshold(self, threshold):
        self._spi.set_param(OCD_TH, 0x1F & threshold)

    def getOCThreshold(self):
        return self._spi.get_param(OCD_TH) & 0x1F

    def setPWMFreq(self, divisor, multiplier):
        configVal = self._spi.get_param(CONFIG)
        configVal &= ~0xE000
        configVal &= ~0x1C00
        configVal |= ((0xE000 & divisor) | (0x1C00 & multiplier))
        self._spi.set_param(CONFIG, configVal)

    def getPWMFreqDivisor(self):
        return int(self._spi.get_param(CONFIG) & 0xE000)

    def getPWMFreqMultiplier(self):
        return int(self._spi.get_param(CONFIG) & 0x1C00)

    def setSlewRate(self, slewRate):
        configVal = self._spi.get_param(GATECFG1)
        configVal &= ~0x00FF
        configVal |= (0x00FF & slewRate)
        self._spi.set_param(GATECFG1, configVal)

    def getSlewRate(self):
        return int(self._spi.get_param(CONFIG) & 0x0300)

    def setOCShutdown(self, OCShutdown):
        configVal = self._spi.get_param(CONFIG)
        configVal &= ~0x0080
        configVal |= (0x0080 & OCShutdown)
        self._spi.set_param(CONFIG, configVal)

    def getOCShutdown(self):
        return int(self._spi.get_param(CONFIG) & 0x0080)

    def setVoltageComp(self, vsCompMode):
        configVal = self._spi.get_param(CONFIG)
        configVal &= ~0x0020
        configVal |= (0x0020 & vsCompMode)
        self._spi.set_param(CONFIG, configVal)

    def getVoltageComp(self):
        return int(self._spi.get_param(CONFIG) & 0x0020)

    def setSwitchMode(self, switchMode):
        configVal = self._spi.get_param(CONFIG)
        configVal &= ~0x0010
        configVal |= (0x0010 & switchMode)
        self._spi.set_param(CONFIG, configVal)

    def getSwitchMode(self):
        return int(self._spi.get_param(CONFIG) & 0x0010)

    def setOscMode(self, oscillatorMode):
        configVal = self._spi.get_param(CONFIG)
        configVal &= ~0x000F
        configVal |= (0x000F & oscillatorMode)
        self._spi.set_param(CONFIG, configVal)

    def getOscMode(self):
        return int(self._spi.get_param(CONFIG) & 0x000F)

    def setAccKVAL(self, kvalInput):
        self._spi.set_param(KVAL_ACC, kvalInput)

    def getAccKVAL(self):
        return self._spi.get_param(KVAL_ACC)

    def setDecKVAL(self, kvalInput):
        self._spi.set_param(KVAL_DEC, kvalInput)

    def getDecKVAL(self):
        return self._spi.get_param(KVAL_DEC)

    def setRunKVAL(self, kvalInput):
        self._spi.set_param(KVAL_RUN, kvalInput)

    def getRunKVAL(self):
        return self._spi.get_param(KVAL_RUN)

    def setHoldKVAL(self, kvalInput):
        self._spi.set_param(KVAL_HOLD, kvalInput)

    def getHoldKVAL(self):
        return self._spi.get_param(KVAL_HOLD)

    def setLoSpdOpt(self, enable):
        temp = self._spi.get_param(MIN_SPEED)
        if enable:
            temp |= 0x00001000
        else:
            temp &= 0xffffefff
        self._spi.set_param(MIN_SPEED, temp)

    def getLoSpdOpt(self):
        return (self._spi.get_param(MIN_SPEED) & 0x00001000) != 0

    def getPos(self):
        temp = self._spi.get_param(ABS_POS)
        if temp & 0x00200000:
            temp |= 0xffc00000
        return temp

    def getMark(self):
        temp = self._spi.get_param(MARK)
        if temp & 0x00200000:
            temp |= 0xffC00000
        return temp

    def run(self, direction, stepsPerSec):
        self._spi.SPIXfer(RUN | direction)
        integerSpeed = int(spdCalc(stepsPerSec))
        if integerSpeed > 0xFFFFF:
            integerSpeed = 0xFFFFF
        byte_int_speed = integerSpeed.to_bytes(length=3, byteorder="little")
        for i in range(3):
            self._spi.SPIXfer(byte_int_speed[i])

    def stepClock(self, direction):
        self._spi.SPIXfer(STEP_CLOCK | direction)

    def move(self, direction, numSteps):
        self._spi.SPIXfer(MOVE | direction)
        if numSteps > 0x3FFFFF:
            numSteps = 0x3FFFFF
        byte_num_steps = numSteps.to_bytes(3,"little")
        for i in range(3):
            self._spi.SPIXfer(byte_num_steps[i])

    def goTo(self, pos):
        self._spi.SPIXfer(GOTO)
        if pos > 0x3FFFFF:
            pos = 0x3FFFFF
        byte_pos = pos.to_bytes(length=3, byteorder="little")
        for i in range(3):
            self._spi.SPIXfer(byte_pos[i])

    def goToDir(self, direction, pos):
        self._spi.SPIXfer(GOTO_DIR | direction)
        if pos > 0x3FFFFF:
            pos = 0x3FFFFF

        byte_pos = pos.to_bytes(length=3, byteorder="little")
        for i in range(3):
            self._spi.SPIXfer(byte_pos[i])

    def goUntil(self, action, direction, stepsPerSec):
        self._spi.SPIXfer(GO_UNTIL | action | direction)
        integerSpeed = int(spdCalc(stepsPerSec))
        if integerSpeed > 0x3FFFFF:
            integerSpeed = 0x3FFFFF
        byte_integer = integerSpeed.to_bytes(length=3, byteorder="little")
        for i in range(3):
            self._spi.SPIXfer(byte_integer[i])

    def releaseSw(self, action, direction):
        self._spi.SPIXfer(RELEASE_SW | action | direction)

    def goHome(self):
        self._spi.SPIXfer(GO_HOME)

    def goMark(self):
        self._spi.SPIXfer(GO_MARK)

    def setMark(self, newMark):
        self._spi.set_param(MARK, newMark)

    def setPos(self, newPos):
        self._spi.set_param(ABS_POS, newPos)

    def resetPos(self):
        self._spi.SPIXfer(RESET_POS)

    def resetDev(self):
        self._spi.SPIXfer(RESET_DEVICE)

    def softStop(self):
        self._spi.SPIXfer(SOFT_STOP)

    def hardStop(self):
        self._spi.SPIXfer(HARD_STOP)

    def softHiZ(self):
        self._spi.SPIXfer(SOFT_HIZ)

    def hardHiZ(self):
        self._spi.SPIXfer(HARD_HIZ)

    def getStatus(self):
        self._spi.SPIXfer(GET_STATUS)
        temp_ba = bytearray(2)
        temp_ba[1] = self._spi.SPIXfer(0)[0]
        temp_ba[0] = self._spi.SPIXfer(0)[0]
        return temp_ba
