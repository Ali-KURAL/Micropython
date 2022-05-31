from machine import I2C, Pin
from micropython import const
import utime 
MCP_4461_DEFAULT_ADDRESS = 0x2F

MCP_4461_VOLATILE_WIPER0 = const(0x00)
MCP_4461_VOLATILE_WIPER1 = const(0x01)
MCP_4461_NONVOLATILE_WIPER0 = const(0x02)
MCP_4461_NONVOLATILE_WIPER1 = const(0x03)
MCP_4461_TCON0 = const(0x04)
MCP_4461_STATUS = const(0x05)

MCP_4461_ALL_WIPERS = const(0xFF)

MCP_4461_DATA_EEPROM0 = const(0x06)
MCP_4461_DATA_EEPROM1 = const(0x07)
MCP_4461_DATA_EEPROM2 = const(0x08)
MCP_4461_DATA_EEPROM3 = const(0x09)
MCP_4461_DATA_EEPROM4 = const(0x0A)
MCP_4461_DATA_EEPROM5 = const(0x0B)
MCP_4461_DATA_EEPROM6 = const(0x0C)
MCP_4461_DATA_EEPROM7 = const(0x0D)
MCP_4461_DATA_EEPROM8 = const(0x0E)
MCP_4461_DATA_EEPROM9 = const(0x0F)


class I2C_COM:
    def __init__(self, address, i2c):
        self._address = address
        self._i2c: I2C = i2c

    def regRead(self, reg: int):
        if 0x00 < reg < 0x0F:
            reg_byte = (reg << 4) | 0b00001100
            return int.from_bytes(self._i2c.readfrom_mem(self._address, reg_byte, 2), 'big') & 0xFF

    def regWrite(self, reg: int, value):
        if value < 0:
            value = 0
        if value > 257:
            value = 257
        if 0x00 < reg < 0x0F:
            cmd_byte = ((reg << 4) & 0b11110000) | (((value & 0x01FF) >> 8) & 0b00000011)
            data_byte = value
            self._i2c.writeto(self._address, bytearray([cmd_byte,data_byte]))
            utime.sleep_ms(10)
        else:
            return 0



class MCP4xx1:
    def __init__(self, i2c_id: int, sda: int, scl: int, i2c_address: int = MCP_4461_DEFAULT_ADDRESS):
        self._i2c = I2C_COM(i2c_address, I2C(i2c_id, scl=Pin(scl), sda=Pin(sda)))
    
    @property
    def status(self):
        return self._i2c.regRead(MCP_4461_STATUS)
    
    @property
    def wiper1(self):
        return self._i2c.regRead(MCP_4461_NONVOLATILE_WIPER1)

    @wiper1.setter
    def wiper1(self, value: int):
        self._i2c.regWrite(MCP_4461_NONVOLATILE_WIPER1, value)

    @property
    def wiper0(self):
        return self._i2c.regRead(MCP_4461_NONVOLATILE_WIPER0)

    @wiper0.setter
    def wiper0(self, value: int):
        self._i2c.regWrite(MCP_4461_NONVOLATILE_WIPER0, value)

    def openCircuit(self):
        return self._i2c.regWrite(MCP_4461_TCON0, 0x0088)

    def enableOutput(self):
        return self._i2c.regWrite(MCP_4461_TCON0, 0x00FF)
