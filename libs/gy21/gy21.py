"""
   ->See the datasheet
   ____|___________________________________|_____
       | temp_meas         ->       0xE3   |
       | humidity_meas     ->       0xE5   |
       | write_user        ->       0xE6   |
       | read_user         ->       0xE7   |
       | soft_reset        ->       0xFE   |
       | pressure_xlsb     ->       0xF9   |
   ____|___________________________________|_____
"""
GY21_ADDRESS = 0x40


def crc8check(value):
    remainder = ((value[0] << 8) + value[1]) << 8
    remainder |= value[2]

    divisor = 0x988000

    for i in range(0, 16):
        if remainder & 1 << (23 - i):
            remainder ^= divisor

        divisor = divisor >> 1

    if remainder == 0:
        return True
    else:
        return False


class GY21:
    def __init__(self, i2c=None, address=None):
        self._address = address
        self._i2c = i2c
        if address is None:
            self.scanI2CAddress(i2c)
        else:
            self._address = address

    def scanI2CAddress(self, i2c):
        """scans I2C adresses of the gy-21"""
        print('Scan i2c bus...')
        devices = i2c.scan()
        if devices:
            for d in devices:
                print("Decimal address: ", d, " | Hex address: ", hex(d))
                if d is GY21_ADDRESS:
                    print("Connected decimal address: ", d)
                    self._address = d
                    return
        else:
            raise ValueError("No device found !")

    @property
    def temperature(self):
        temp_val = self._i2c.readfrom_mem(self._address, 0xE3, 3)

        raw_temp_val = (temp_val[0] << 8) + temp_val[1]
        raw_temp_val = raw_temp_val & 0xFFFC
        return (-46.85 + (175.72 * (raw_temp_val / pow(2, 16))))

    @property
    def humidity(self):
        hum_val = self._i2c.readfrom_mem(self._address, 0xE5, 3)

        raw_hum_val = (hum_val[0] << 8) + hum_val[1]
        raw_hum_val = raw_hum_val & 0xFFFC
        return (-6 + (125.0 * raw_hum_val / pow(2, 16)))
