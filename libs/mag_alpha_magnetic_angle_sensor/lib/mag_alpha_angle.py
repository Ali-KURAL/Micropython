import time

from machine import SPI, Pin


class SPI_COM:
    def __init__(self, spi_id, cs, sck, mosi, miso):
        self._spi = SPI(spi_id,
                        baudrate=10000000,
                        polarity=0,
                        phase=1,
                        bits=8,
                        firstbit=SPI.MSB,
                        sck=Pin(sck),
                        mosi=Pin(mosi),
                        miso=Pin(miso))
        self._cs = Pin(cs, Pin.OUT)
        self._cs.value(1)

    def transfer(self, write_bytes):
        self._cs.value(0)
        self._spi.write(bytearray(write_bytes[0]))
        rx_data = self._spi.read(2)
        self._cs.value(1)
        return rx_data


class MagAlpha:
    def __init__(self, spi_id, cs_pin, sck_pin, mosi_pin, miso_pin):
        self.spiClockFreqInHz = 1000000
        self.spi = SPI_COM(spi_id, cs_pin, sck_pin, mosi_pin, miso_pin)
        self.__rawToDegreeRatio = 360.0 / 65536.0

    def readAngle(self, print_en=False):
        """Return the angle [0-65535] (raw sensor output value)."""
        response = self.spi.transfer([0x00, 0x00])
        angularPositionRaw = (response[0] << 8) + response[1]
        if print_en:
            print('Angular Position [raw] : {0}'.format(angularPositionRaw))
        return angularPositionRaw

    def readAngleInDegree(self, printEnabled=False):
        """Return the angle in degree [0-360] (raw sensor output converted in degree)."""
        response = self.spi.transfer([0x00, 0x00])
        angularPositionRaw = (response[0] << 8) + response[1]
        angularPositionDegree = float(angularPositionRaw) * self.__rawToDegreeRatio
        if printEnabled:
            print('Angular Position [degree] : {0}'.format(angularPositionDegree))
        return angularPositionDegree

    def readAngleAdvanced(self, printEnabled=False):
        """Return the angle in raw and degree format."""
        response = self.spi.transfer([0x00, 0x00])
        angularPositionRaw = (response[0] << 8) + response[1]
        angularPositionDegree = float(angularPositionRaw) * self.__rawToDegreeRatio
        if printEnabled:
            print('Angular Position [raw] : {0} \t, [degree] : {1}'.format(angularPositionRaw, angularPositionDegree))
        return angularPositionRaw, angularPositionDegree

    def readRegister(self, address, printEnabled=False):
        """Return sensor register value."""
        command = 0b01000000 | (address & 0x1F)
        self.spi.transfer([command, 0x00])
        response = self.spi.transfer([0x00, 0x00])
        registerValue = response[0]
        if printEnabled:
            print('Read Register [{0}] \t=\t{1}'.format(address, registerValue))
        return registerValue

    def writeRegister(self, address, value, printEnabled=False):
        """Return sensor written register value."""
        command = 0b10000000 | (address & 0x1F)
        registerWriteValue = (value & 0xFF)
        self.spi.transfer([command, registerWriteValue])
        # wait for 20ms
        time.sleep(0.02)
        response = self.spi.transfer([0x00, 0x00])
        registerReadValue = response[0]
        if printEnabled:
            print('Write Register [{0}] \t=\t{1}, \tReadback Value = {2}'.format(address, registerWriteValue,
                                                                                 registerReadValue))
        return registerReadValue
