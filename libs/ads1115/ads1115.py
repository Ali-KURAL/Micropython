from machine import I2C, Pin
import time

ADS1115_I2C_ADDRESS_PRIM = 0x48

# ADS1115 Register Map
ADS1115_REG_POINTER_CONVERT = 0x00  # Conversion register
ADS1115_REG_POINTER_CONFIG = 0x01  # Configuration register
ADS1115_REG_POINTER_LOWTHRESH = 0x02  # Lo_thresh register
ADS1115_REG_POINTER_HITHRESH = 0x03  # Hi_thresh register

ADS1115_REG_CONFIG_OS_NOEFFECT = 0x00  # No effect
ADS1115_REG_CONFIG_OS_SINGLE = 0x80  # Begin a single conversion
ADS1115_REG_CONFIG_MUX_DIFF_0_1 = 0x00  # Differential P = AIN0, N = AIN1 (default)
ADS1115_REG_CONFIG_MUX_DIFF_0_3 = 0x10  # Differential P = AIN0, N = AIN3
ADS1115_REG_CONFIG_MUX_DIFF_1_3 = 0x20  # Differential P = AIN1, N = AIN3
ADS1115_REG_CONFIG_MUX_DIFF_2_3 = 0x30  # Differential P = AIN2, N = AIN3
ADS1115_REG_CONFIG_MUX_SINGLE_0 = 0x40  # Single-ended P = AIN0, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_1 = 0x50  # Single-ended P = AIN1, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_2 = 0x60  # Single-ended P = AIN2, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_3 = 0x70  # Single-ended P = AIN3, N = GND
ADS1115_REG_CONFIG_PGA_6_144V = 0x00  # +/-6.144V range = Gain 2/3
ADS1115_REG_CONFIG_PGA_4_096V = 0x02  # +/-4.096V range = Gain 1
ADS1115_REG_CONFIG_PGA_2_048V = 0x04  # +/-2.048V range = Gain 2 (default)
ADS1115_REG_CONFIG_PGA_1_024V = 0x06  # +/-1.024V range = Gain 4
ADS1115_REG_CONFIG_PGA_0_512V = 0x08  # +/-0.512V range = Gain 8
ADS1115_REG_CONFIG_PGA_0_256V = 0x0A  # +/-0.256V range = Gain 16
ADS1115_REG_CONFIG_MODE_CONTIN = 0x00  # Continuous conversion mode
ADS1115_REG_CONFIG_MODE_SINGLE = 0x01  # Power-down single-shot mode (default)
ADS1115_REG_CONFIG_DR_8SPS = 0x00  # 8 samples per second
ADS1115_REG_CONFIG_DR_16SPS = 0x20  # 16 samples per second
ADS1115_REG_CONFIG_DR_32SPS = 0x40  # 32 samples per second
ADS1115_REG_CONFIG_DR_64SPS = 0x60  # 64 samples per second
ADS1115_REG_CONFIG_DR_128SPS = 0x80  # 128 samples per second (default)
ADS1115_REG_CONFIG_DR_250SPS = 0xA0  # 250 samples per second
ADS1115_REG_CONFIG_DR_475SPS = 0xC0  # 475 samples per second
ADS1115_REG_CONFIG_DR_860SPS = 0xE0  # 860 samples per second
ADS1115_REG_CONFIG_CMODE_TRAD = 0x00  # Traditional comparator with hysteresis (default)
ADS1115_REG_CONFIG_CMODE_WINDOW = 0x10  # Window comparator
ADS1115_REG_CONFIG_CPOL_ACTVLOW = 0x00  # ALERT/RDY pin is low when active (default)
ADS1115_REG_CONFIG_CPOL_ACTVHI = 0x08  # ALERT/RDY pin is high when active
ADS1115_REG_CONFIG_CLAT_NONLAT = 0x00  # Non-latching comparator (default)
ADS1115_REG_CONFIG_CLAT_LATCH = 0x04  # Latching comparator
ADS1115_REG_CONFIG_CQUE_1CONV = 0x00  # Assert ALERT/RDY after one conversions
ADS1115_REG_CONFIG_CQUE_2CONV = 0x01  # Assert ALERT/RDY after two conversions
ADS1115_REG_CONFIG_CQUE_4CONV = 0x02  # Assert ALERT/RDY after four conversions
ADS1115_REG_CONFIG_CQUE_NONE = 0x03  # Disable the comparator and put ALERT/RDY in high state (default)
    

class I2C_COM:
    def __init__(self, address, i2c: I2C):
        self._i2c = i2c
        self._address = address

    def writeToMemMany(self, reg, values):
        ba = bytearray(values)
        print(ba)
        self._i2c.writeto_mem(self._address, reg, ba)

    def readUnsigned16B(self, reg):
        """Read a unsigned 16-bit value from the specific register"""
        read_data = self._i2c.readfrom_mem(self._address, reg, 2)
        result = (read_data[0] << 8) + read_data[1]
        return result

    def readSigned16B(self, reg):
        """Read a signed 16-bit value from the specific register"""
        result = self.readUnsigned16B(reg)
        if result > 32767:
            result -= 65536
        return result


class ADS1115:
    def __init__(self, i2c_port, scl, sda, i2c_address=ADS1115_I2C_ADDRESS_PRIM):
        i2c_obj = I2C(i2c_port, scl=Pin(scl), sda=Pin(sda))
        print(i2c_obj.scan())
        self._i2c = I2C_COM(i2c_address, i2c_obj)

    def config_single_ended(self, channel):
        """Select the Configuration Register data from the given provided value above"""
        config = None
        if channel == 0:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_0 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 1:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_1 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN,
                ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 2:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_2 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 3:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_3 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]

        if config:
            self._i2c.writeToMemMany(ADS1115_REG_POINTER_CONFIG, config)
        else:
            raise ValueError("There are only 4 channel :\n{0,1,2,3}")

    def config_differential(self, channel):
        """Select the Configuration Register data from the given provided value above"""
        config = None
        if channel == 0:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_DIFF_0_1 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 1:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_DIFF_0_3 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 2:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_DIFF_1_3 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif channel == 3:
            config = [
                ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_DIFF_2_3 | ADS1115_REG_CONFIG_PGA_4_096V |
                ADS1115_REG_CONFIG_MODE_CONTIN, ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]

        if config:
            self._i2c.writeToMemMany(ADS1115_REG_POINTER_CONFIG, config)
        else:
            raise ValueError("There are only 4 channel :\n{0,1,2,3}")

    def read_adc_single_ended(self, channel):
        """Read data back from ADS1115_REG_POINTER_CONVERT(0x00), 2 bytes
        raw_adc MSB, raw_adc LSB"""
        self.config_single_ended(channel)
        time.sleep(0.1)
        adc = self._i2c.readSigned16B(ADS1115_REG_POINTER_CONVERT)
        return adc

    def read_adc_differential(self, channel):
        self.config_differential(channel)
        time.sleep(0.1)
        adc = self._i2c.readSigned16B(ADS1115_REG_POINTER_CONVERT)
        return adc
