from machine import SPI, Pin
import math
import time

# Register and other constant values:
CONFIG_REGISTER = 0x00
CONFIG_BIAS = 0x80
CONFIG_MODE_AUTO = 0x40
CONFIG_MODE_OFF = 0x00

CONFIG_1SHOT = 0x20

CONFIG_3WIRE = 0x10
CONFIG_2_4WIRE = 0x00

CONFIG_FAULT_STATUS = 0x02

CONFIG_FILTER_50HZ = 0x01
CONFIG_FILTER_60HZ = 0x00

RTD_MSB_REGISTER = 0x01
RTD_LSB_REG = 0x02
H_FAULT_MSB_REG = 0x03
H_FAULT_LSB_REG = 0x04
L_FAULT_MSB_REG = 0x05
L_FAULT_LSB_REG = 0x06

FAULT_STATUS_REG = 0x07
FAULT_HIGH_THRESHOLD = 0x80
FAULT_LOW_THRESHOLD = 0x40
FAULT_REF_IN_LOW = 0x20
FAULT_REF_IN_HIGH = 0x10
FAULT_RTD_IN_LOW = 0x08
FAULT_OVUV = 0x04
_RTD_A = 3.9083e-3
_RTD_B = -5.775e-7


class AR_SPI:
    def __init__(self, peripheral, mosi, miso, sck, cs):
        self._spi = SPI(peripheral,
                        baudrate=100000,
                        polarity=0,
                        phase=1,
                        firstbit=SPI.MSB,
                        mosi=Pin(mosi),
                        miso=Pin(miso),
                        sck=Pin(sck))
        self._cs = Pin(cs, mode=Pin.OUT)

    def read_u8(self, address):
        self._cs.off()
        self._spi.write(bytes([address]))
        config = self._spi.read(1)
        self._cs.on()
        return int.from_bytes(config, "little")

    def read_u16(self, address):
        self._cs.off()
        self._spi.write(bytes([address]))
        MSB = self._spi.read(1)
        LSB = self._spi.read(1)
        self._cs.on()
        return (MSB[0] << 8) + LSB[0]

    def write_u8(self, address, value):
        self._cs.off()
        buff = bytearray(2)
        buff[0] = (address | 0x80) & 0xFF
        buff[1] = value & 0xFF
        self._spi.write(buff)
        self._cs.on()


class MAX31865:
    """Driver for the MAX31865 thermocouple amplifier.
    :param ~peripheral: SPI peripheral
    :param ~mosi: SPI mosi pin(int)
    :param ~miso: SPI miso pin(int)
    :param ~sck: SPI sck pin(int)
    :param ~cs: Chip Select
    :param int rtd_nominal: RTD nominal value. Defaults to :const:`100`
    :param int ref_resistor: Reference resistance. Defaults to :const:`430.0`
    :param int wires: Number of wires. Defaults to :const:`2`
    :param int filter_frequency: . Filter frequency. Default to :const:`60`
    """

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!

    def __init__(
            self,
            peripheral,
            mosi,
            miso,
            sck,
            cs,
            rtd_nominal=100,
            ref_resistor=430.0,
            wires=4,
            filter_frequency=60
    ):
        self.rtd_nominal = rtd_nominal
        self.ref_resistor = ref_resistor
        self._spi = AR_SPI(peripheral, mosi, miso, sck, cs)
        # Set 50Hz or 60Hz filter.
        config = self._spi.read_u8(CONFIG_REGISTER)
        if filter_frequency is 50:
            config |= CONFIG_FILTER_50HZ
        elif filter_frequency is 60:
            config &= CONFIG_FILTER_60HZ
        else:
            raise ValueError("Filter frequency should be 50 or 60!")

        # Set wire config register based on the number of wires specified.
        if wires is 3:
            config |= CONFIG_3WIRE
        elif wires in (2, 4):
            # 2 or 4 wire
            config &= ~CONFIG_2_4WIRE
        else:
            raise ValueError("Wires can be 2, 3, or 4!")

        self._spi.write_u8(CONFIG_REGISTER, config)

    @property
    def bias(self):
        return bool(self._spi.read_u8(CONFIG_REGISTER) & CONFIG_BIAS)

    @bias.setter
    def bias(self, val):
        config = self._spi.read_u8(CONFIG_REGISTER)
        if val:
            config |= CONFIG_BIAS  # Enable bias.
        else:
            config &= ~CONFIG_BIAS  # Disable bias.
        self._spi.write_u8(CONFIG_REGISTER, config)

    @property
    def auto_convert(self):
        return bool(self._spi.read_u8(CONFIG_REGISTER) & CONFIG_MODE_AUTO)

    @auto_convert.setter
    def auto_convert(self, val):
        config = self._spi.read_u8(CONFIG_REGISTER)
        if val:
            config |= CONFIG_MODE_AUTO  # Enable auto convert.
        else:
            config &= ~CONFIG_MODE_AUTO  # Disable auto convert.
        self._spi.write_u8(CONFIG_REGISTER, config)

    @property
    def fault(self):
        faults = self._spi.read_u8(FAULT_STATUS_REG)
        high_thresh = bool(faults & FAULT_HIGH_THRESHOLD)
        low_thresh = bool(faults & FAULT_LOW_THRESHOLD)
        ref_in_low = bool(faults & FAULT_REF_IN_LOW)
        ref_in_high = bool(faults & FAULT_REF_IN_HIGH)
        rtd_in_low = bool(faults & FAULT_RTD_IN_LOW)
        ovuv = bool(faults & FAULT_OVUV)
        return high_thresh, low_thresh, ref_in_low, ref_in_high, rtd_in_low, ovuv

    def clear_faults(self):
        """Clear any fault state previously detected by the sensor."""
        config = self._spi.read_u8(CONFIG_REGISTER)
        config &= ~0x2C
        config |= CONFIG_FAULT_STATUS
        self._spi.write_u8(CONFIG_REGISTER, config)

    def read_rtd(self):
        self.clear_faults()
        self.bias = True
        time.sleep(0.01)
        config = self._spi.read_u8(CONFIG_REGISTER)
        config |= CONFIG_1SHOT
        self._spi.write_u8(CONFIG_REGISTER, config)
        time.sleep(0.065)
        rtd = self._spi.read_u16(RTD_MSB_REGISTER)
        self.bias = False
        # Remove fault bit.
        rtd >>= 1
        return rtd

    @property
    def resistance(self):
        resistance = self.read_rtd()
        resistance /= 32768
        resistance *= self.ref_resistor
        return resistance

    @property
    def temperature(self):
        raw_reading = self.resistance
        Z1 = -_RTD_A
        Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
        Z3 = (4 * _RTD_B) / self.rtd_nominal
        Z4 = 2 * _RTD_B
        temp = Z2 + (Z3 * raw_reading)
        temp = (math.sqrt(temp) + Z1) / Z4
        if temp >= 0:
            return temp

        # For the following math to work, nominal RTD resistance must be normalized to 100 ohms
        raw_reading /= self.rtd_nominal
        raw_reading *= 100

        rpoly = raw_reading
        temp = -242.02
        temp += 2.2228 * rpoly
        rpoly *= raw_reading  # square
        temp += 2.5859e-3 * rpoly
        rpoly *= raw_reading  # ^3
        temp -= 4.8260e-6 * rpoly
        rpoly *= raw_reading  # ^4
        temp -= 2.8183e-8 * rpoly
        rpoly *= raw_reading  # ^5
        temp += 1.5243e-10 * rpoly
        return temp

    @property
    def data_error(self):
        full_data_array = [self.temperature, self.resistance]
        full_data_array.extend(self.fault)
        return full_data_array
