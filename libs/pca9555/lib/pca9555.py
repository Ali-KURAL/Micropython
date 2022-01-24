PCA_INPUT = 0
PCA_OUTPUT = 1
PCA_POLARITY = 2
PCA_CONFIG = 3


class I2C_COM:
    def __init__(self, address, i2c):
        self._address = address
        self._i2c = i2c

    def writeToMemMany(self, reg, values):
        """Write bytes to specific register"""
        ba = bytearray(values)
        self._i2c.writeto_mem(self._address, reg, ba)

    def readUnsigned8B(self, reg):
        """Read an unsigned byte from the specific register."""
        return int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 1), 'little') & 0xFF

    def readUnsigned16B(self, reg, little_endian=True):
        """Read an unsigned 16-bit value from the specific register"""
        result = int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 2), 'little') & 0xFFFF
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        return result


class PCA9555:
    OUT = 0
    IN = 1
    """
    <---------------------------PINS ARE BCM PINS------------------------------>
    CHECK DATASHEET FOR PINS (https://www.nxp.com/docs/en/data-sheet/PCA9555.pdf)
    IO0_0(BOARD_4)  -- IO0_7(BOARD_11) -> BCM 0 -- BCM 7
    IO1_0(BOARD_13) -- IO1_7(BOARD_20) -> BCM 8 -- BCM 15
    """
    def __init__(self, i2c, i2c_address=0x21):
        self._i2c = I2C_COM(i2c_address, i2c)
        self._gpio_count = 16
        self.direction = self._i2c.readUnsigned16B(PCA_CONFIG << 1)
        self.output_value = self._i2c.readUnsigned16B(PCA_OUTPUT << 1)

    def _update_pin(self, port, pin, value, port_state=None):
        assert 0 <= pin < self._gpio_count, "Pin number %s is invalid, only 0-15 are valid" % pin
        old_state = port_state
        if not port_state:
            old_state = self._i2c.readUnsigned16B(port << 1)

        if value == 0:
            new_state = old_state & ~(1 << pin)
        elif value == 1:
            new_state = old_state | (1 << pin)
        else:
            raise ValueError("Value is %s must be 1 or 0" % value)

        new_state_arr = [new_state & 0xFF, new_state >> 8]
        self._i2c.writeToMemMany(port << 1, new_state_arr)
        return new_state

    # Pin direction
    def set_pin(self, pin, mode):
        self.direction = self._update_pin(PCA_CONFIG, pin, mode, self.direction)
        return self.direction

    def output(self, pin, value):
        assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        self.output_value = self._update_pin(PCA_OUTPUT, pin, value, self.output_value)
        return self.output_value

    def input(self, pin):
        assert self.direction & (1 << pin) != 0, "Pin %s not set to input" % pin
        value = self._i2c.readUnsigned8B(PCA_INPUT << 1)
        return value & (1 << pin)
