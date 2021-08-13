import utime
import struct

SEESAW_I2C_ADDR_PRIM = 0x36

SEESAW_REGISTER_CHIP_ID = 0x55


class I2C_SS:
    def __init__(self, address, i2c=None):
        self._i2c = i2c
        self._address = address

    def writeTo(self, register_base, register, val=None):
        val_bytearray = bytearray()
        val_bytearray.append(register_base)
        val_bytearray.append(register)
        if val is not None:
            val_bytearray.append(val)
        self._i2c.writeto(self._address, val_bytearray)

    def readTo(self, register_base, register, buffer):
        self.writeTo(register_base, register)
        utime.sleep_ms(5)
        self._i2c.readfrom_into(self._address, buffer)
        return buffer


class Seesaw:
    def __init__(self, i2c=None, i2c_address=None):
        self._address = i2c_address
        if i2c_address is None:
            self.scanI2CAddress(i2c)
        else:
            self._address = i2c_address
        self._i2c = I2C_SS(self._address, i2c)    

    def scanI2CAddress(self, i2c):
        """scans I2C adresses of the gy-21"""
        print('Scan i2c bus...')
        devices = i2c.scan()
        if devices:
            for d in devices:
                print("Decimal address: ", d, " | Hex address: ", hex(d))
                if d is SEESAW_I2C_ADDR_PRIM:
                    print("Connected decimal address: ", d)
                    self._address = d
                    return
        else:
            raise ValueError("No device found !")

    def software_reset(self):
        self._i2c.writeTo(0x00, 0x7F, 0xFF)
        utime.sleep_ms(500)
        chip_id_ba = bytearray(1)
        self._i2c.readTo(0x00, 0x01, chip_id_ba)
        chip_id = chip_id_ba[0]
        if chip_id != SEESAW_REGISTER_CHIP_ID:
            raise RuntimeError("SeeSaw hardware ID returned (0x{:x}) is not "
                               "correct! Expected 0x{:x}. Please check your wiring."
                               .format(chip_id, 0x55))

    @property
    def temperature(self):
        buffer = bytearray(4)
        self._i2c.readTo(0x00, 0x04, buffer)
        buffer[0] = buffer[0] & 0x3F
        buf_int = struct.unpack(">I", buffer)[0]
        return buf_int * 0.00001525878

    @property
    def moisture(self):
        buffer = bytearray(2)
        self._i2c.readTo(0x0F, 0x10, buffer)
        buf_short = struct.unpack(">H", buffer)[0]
        utime.sleep_ms(1)

        invalid = 0
        while buf_short > 4095:
            self._i2c.readTo(0x0F, 0x10, buffer)
            buf_short = struct.unpack(">H", buffer)[0]
            utime.sleep_ms(1)
            invalid += 1
            if invalid > 5:
                raise RuntimeError("Could not get a valid moisture reading.")

        return buf_short
