from utime import sleep_us

"""
    ->See the datasheet
    ____|___________________________________|_____
        | power_off         ->       0x00   |
        | power_on          ->       0x01   |
        | reset             ->       0x07   |
        | cont_h_res_mode   ->       0x10   |
        | cont_h_res_mode2  ->       0x11   |
        | cont_l_res_mode   ->       0x13   |
        | onet_h_res_mode   ->       0x20   |
        | onet_h_res_mode2  ->       0x21   |
        | onet_l_res_mode   ->       0x23   |
    ____|___________________________________|_____
"""

BH1750_I2C_ADDRESS_PRIM = 0x23;
BH1750_I2C_ADDRESS_SEC = 0x5C;

MODE_DICT = {'CHR': 0x10, 'CHR2': 0x11, 'CLR': 0x13, 'OHR': 0x20, 'OHR2': 0x21, 'OLR': 0x23}

class BH1750:
    def __init__(self, i2c=None, address=None):
        if address == None:
            self._address = BH1750_I2C_ADDRESS_PRIM
            self.scanI2CAddress(i2c)
        else:
            self._address = address
        self._mode = None
        self._i2c = i2c
        self.power_off()
        self.reset()
        self.power_on()

    def scanI2CAddress(self, i2c):
        """scans I2C adresses of the bme280 if finds 2 device then automatically select the primary adress"""
        print('Scan i2c bus...')
        devices = i2c.scan()

        if devices:
            for d in devices:
                print("Decimal address: ", d, " | Hex address: ", hex(d))
                if d in [BH1750_I2C_ADDRESS_PRIM, BH1750_I2C_ADDRESS_SEC]:
                    print("Connected decimal address: ", d)
                    self._address = d
                    return
        else:
            raise ValueError("I2C object is mandatory")

    def power_on(self):
        self._i2c.writeto(self._address, bytes([0x01]))

    def power_off(self):
        self._i2c.writeto(self._address, bytes([0x00]))

    def reset(self):
        self._i2c.writeto(self._address, bytes([0x07]))

    def set_mode(self,mode_code = None):
        if mode_code == None:
            print("Please write a mode code\n"
                  "->Mode codes :\n"
                  "\'CHR\' for Continuous High Resolution Mode\n"
                  "\'CHR2\' for Continuous High Resolution Mode 2\n"
                  "\'CLR\' for Continuous Low Resolution Mode\n"
                  "\'OHR\' for One Time High Resolution Mode\n"
                  "\'OHR2\' for One Time High Resolution Mode\n"
                  "\'OLR\' for One Time Low Resolution Mode\n")
        else:
            new_mode = MODE_DICT.get(mode_code)
            if new_mode is None :
                raise ValueError("\nPlease write an available mode code\n"
                  "->Mode codes :\n"
                  "\'CHR\' for Continuous High Resolution Mode\n"
                  "\'CHR2\' for Continuous High Resolution Mode 2\n"
                  "\'CLR\' for Continuous Low Resolution Mode\n"
                  "\'OHR\' for One Time High Resolution Mode\n"
                  "\'OHR2\' for One Time High Resolution Mode\n"
                  "\'OLR\' for One Time Low Resolution Mode\n")
            if new_mode & 0x20:
                self._mode = new_mode;
                self._i2c.writeto(self._address, bytes([self._mode]))
            else:
                if new_mode != self._mode:
                    self._mode = new_mode;
                    self._i2c.writeto(self._address, bytes([self._mode]))




    def lux(self):
        if self._mode is None:
            raise ValueError("\nNo mode selected !\nPlease chose a mode with set_mode method !")
            return

        sleep_us(24 if self._mode in (0x13, 0x23) else 180)
        data = self._i2c.readfrom(self._address, 2)
        factor = 2.0 if self._mode in (0x11, 0x21) else 1.0

        return (data[0] << 8 | data[1]) / (1.2 * factor)