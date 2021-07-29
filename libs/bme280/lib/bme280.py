from machine import I2C
import time

#  BME280 Default I2C address
BME280_I2C_ADDRESS_PRIM = 0x76
BME280_I2C_ADDRESS_SEC = 0x77

#  BME280 Operating Modes
BME280_OSAMPLE_1 = 1
BME280_OSAMPLE_2 = 2
BME280_OSAMPLE_4 = 3
BME280_OSAMPLE_8 = 4
BME280_OSAMPLE_16 = 5

BME280_REGISTER_CHIP_ID = 0xD0
BME280_REGISTER_VERSION = 0xD1
BME280_REGISTER_SOFT_RESET = 0xE0

BME280_REGISTER_CONTROL_HUM = 0xF2
BME280_REGISTER_CONTROL = 0xF4

BME280_REGISTER_CONFIG = 0xF5
BME280_REGISTER_PRESSURE_DATA = 0xF7
BME280_REGISTER_TEMP_DATA = 0xFA
BME280_REGISTER_HUMIDITY_DATA = 0xFD


class BME280_I2C_COM:
    def __init__(self, address, i2c):
        self._address = address
        self._i2c = i2c

    def writeToMem8B(self, reg, val):
        """Write an 8-bit value to the specific register."""
        val_bytearray = bytearray(1)
        val_bytearray[0] = val & 0xFF
        self._i2c.writeto_mem(self._address, reg, val_bytearray)

    def readUnsigned8B(self, reg):
        """Read an unsigned byte from the specific register."""
        return int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 1), 'little') & 0xFF

    def readSigned8B(self, reg):
        """Read a signed byte from the specific register."""
        result = self.readUnsigned8B(reg)
        if result > 127:
            result -= 256
        return result

    def readUnsigned16B(self, reg, little_endian=True):
        """Read a unsigned 16-bit value from the specific register"""
        result = int.from_bytes(self._i2c.readfrom_mem(self._address, reg, 2), 'little') & 0xFFFF
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        return result

    def readSigned16B(self, reg, little_endian=True):
        """Read a signed 16-bit value from the specific register"""
        result = self.readUnsigned16B(reg, little_endian)
        if result > 32767:
            result -= 65536
        return result

    def readUnsigned16LE(self, reg):
        """Read an unsigned 16-bit value from the specific register, in little endian byte order."""
        return self.readUnsigned16B(reg)

    def readSigned16LE(self, reg):
        """Read a signed 16-bit value from the specific register, in little endian byte order."""
        return self.readSigned16B(reg)


class BME280:
    def __init__(self, mode=BME280_OSAMPLE_1, i2c=None, i2c_address=None):
        """
        Checks the mode value is in the bme280 mod values
        """
        if mode not in [BME280_OSAMPLE_1, BME280_OSAMPLE_2, BME280_OSAMPLE_4, BME280_OSAMPLE_8, BME280_OSAMPLE_16]:
            raise ValueError('Unexpected mode value {0}. Set mode to one of ',
                             'BME280_ULTRA_LOW_POWER, BME280_STANDARD, BME280_HIGH_RES, or ',
                             'BME280_ULTRA_HIGH_RES'.format(mode))

        self._mode = mode

        if i2c_address is None:
            self._address = BME280_I2C_ADDRESS_PRIM
            self.scanI2CAddress(i2c)
        else:
            self._address = i2c_address

        self._i2c = BME280_I2C_COM(self._address, i2c)
        self._calibrate_digits()

        # Set the bme280 address to 0x3F
        self._i2c.writeToMem8B(BME280_REGISTER_CONTROL, 0x3F)
        self.t_fine = 0

    def scanI2CAddress(self, i2c):
        """scans I2C adresses of the bme280
            if finds 2 device then automatically select the primary adress"""
        print('Scan i2c bus...')
        devices = i2c.scan()

        if devices:
            for d in devices:
                print("Decimal address: ", d, " | Hex address: ", hex(d))
                if d in [BME280_I2C_ADDRESS_PRIM, BME280_I2C_ADDRESS_SEC]:
                    print("Connected decimal address: ", d)
                    self._address = d
                    return
        else:
            raise ValueError("I2C object is mandatory")

    """
       ->See the datasheet
       ____|___________________________________|____
           | dig_t1_reg        ->       0x88   |
           | dig_t2_reg        ->       0x8A   |
           | dig_t3_reg        ->       0x8C   |
           | dig_p1_reg        ->       0x8E   |
           | dig_p2_reg        ->       0x90   |
           | dig_p3_reg        ->       0x92   |
           | dig_p4_reg        ->       0x94   |
           | dig_p5_reg        ->       0x96   |
           | dig_p6_reg        ->       0x98   |
           | dig_p7_reg        ->       0x9A   |
           | dig_p8_reg        ->       0x9C   |
           | dig_p9_reg        ->       0x9E   |
       ____|___________________________________|____
    """

    def _calibrate_digits(self):
        self.dig_T1 = self._i2c.readUnsigned16LE(0x88)
        self.dig_T2 = self._i2c.readSigned16LE(0x8A)
        self.dig_T3 = self._i2c.readSigned16LE(0x8C)

        self.dig_P1 = self._i2c.readUnsigned16LE(0x8E)
        self.dig_P2 = self._i2c.readSigned16LE(0x90)
        self.dig_P3 = self._i2c.readSigned16LE(0x92)
        self.dig_P4 = self._i2c.readSigned16LE(0x94)
        self.dig_P5 = self._i2c.readSigned16LE(0x96)
        self.dig_P6 = self._i2c.readSigned16LE(0x98)
        self.dig_P7 = self._i2c.readSigned16LE(0x9A)
        self.dig_P8 = self._i2c.readSigned16LE(0x9C)
        self.dig_P9 = self._i2c.readSigned16LE(0x9E)

        self.dig_H1 = self._i2c.readUnsigned8B(0xA1)
        self.dig_H2 = self._i2c.readSigned16LE(0xE1)
        self.dig_H3 = self._i2c.readUnsigned8B(0xE3)
        self.dig_H6 = self._i2c.readSigned8B(0xE7)

        h4 = self._i2c.readSigned8B(0xE4)
        h4 = (h4 << 24) >> 20
        self.dig_H4 = h4 | (self._i2c.readUnsigned8B(0xE5) & 0x0F)

        h5 = self._i2c.readSigned8B(0xE6)
        h5 = (h5 << 24) >> 20
        self.dig_H5 = h5 | (self._i2c.readUnsigned8B(0xE5) >> 4 & 0x0F)

    """
    ->See the datasheet
    ____|___________________________________|____
        | humidity_lsb      ->       0xFE   |
        | humidity_msb      ->       0xFD   |
        | temperature_lsb   ->       0xFB   |
        | temperature_msb   ->       0xFA   |
        | temperature_xlsb  ->       0xFC   |
        | pressure_lsb      ->       0xF8   |
        | pressure_msb      ->       0xF7   |
        | pressure_xlsb     ->       0xF9   |
    ____|___________________________________|____
        | ctrl_meas         ->       0xF4   |
        | ctrl_hum          ->       0xFD   |
        | Temperature_data_register  0xFA   |
        | Pressure_data_register     0xF7   |
        | Humidity_data_register     0xFD   |
    ____|___________________________________|____
    """

    def read_temperature(self):
        mode_val = self._mode
        self._i2c.writeToMem8B(0xF2, mode_val)
        mode_val = self._mode << 5 | self._mode << 2 | 1
        self._i2c.writeToMem8B(0xF4, mode_val)

        #   Wait the required time
        sleep_time = 1250 + 2300 * (1 << self._mode)
        sleep_time += 2300 * (1 << self._mode) + 575
        sleep_time += 2300 * (1 << self._mode) + 575
        time.sleep_us(sleep_time)

        #   Read raw temperature
        msb_temp = self._i2c.readUnsigned8B(0xFA)
        lsb_temp = self._i2c.readUnsigned8B(0xFB)
        xlsb_temp = self._i2c.readUnsigned8B(0xFC)

        raw_temp = ((msb_temp << 16) | (lsb_temp << 8) | xlsb_temp) >> 4

        #   Calculate the temperature
        adc_T = raw_temp
        var1 = ((adc_T >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >> 11)
        var2 = (((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2

        return (self.t_fine * 5 + 128) >> 8

    def read_pressure(self):
        #   Read raw pressure
        msb_pres = self._i2c.readUnsigned8B(0xF7)
        lsb_pres = self._i2c.readUnsigned8B(0xF8)
        xlsb_pres = self._i2c.readUnsigned8B(0xF9)
        raw_pres = ((msb_pres << 16) | (lsb_pres << 8) | xlsb_pres) >> 4

        #   Calculate the Pressure
        adc_P = raw_pres
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = (((var1 * var1 * self.dig_P3) >> 8) +
                ((var1 * self.dig_P2) >> 12))
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - adc_P
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        return ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

    def read_humidity(self):
        #   Read raw humidity
        msb_hum = self._i2c.readUnsigned8B(0xFD)
        lsb_hum = self._i2c.readUnsigned8B(0xFE)
        raw_hum = (msb_hum << 8) | lsb_hum

        #   Calculate the Humidity
        adc_h = raw_hum

        h = self.t_fine - 76800
        h = (((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15) *
             (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
               self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        return h >> 12

    """USER FUNCTIONS"""

    def getTemperature(self):
        t = self.read_temperature()
        t_integer = t // 100
        t_fractional = t - t_integer * 100
        return "{}.{:02d}C".format(t_integer, t_fractional)

    def getPressure(self):
        p = self.read_pressure() // 256
        p_integer = p // 100
        p_fractional = p - p_integer * 100
        return "{}.{:02d}hPa".format(p_integer, p_fractional)

    def getHumidity(self):
        h = self.read_humidity()
        h_integer = h // 1024
        h_fractional = h * 100 // 1024 - h_integer * 100
        return "{}.{:02d}%".format(h_integer, h_fractional)
