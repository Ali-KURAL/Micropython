from machine import SPI, Pin

class SPI_COM:
    def __init__(self, spi_id, cs):
        print("MAY BE SOME ERRORS PLEASE USE NEW VERSION")
        self._spi = SPI(spi_id,
                        baudrate=1000000,
                        polarity=0,
                        phase=1,
                        bits=8,
                        firstbit=SPI.MSB)
        self._cs = Pin(cs, Pin.OUT)
        self._cs.value(1)

    def readAngleRaw16B(self):
        msg = bytearray()
        msg.append(0x0000)
        self._cs.value(0)
        self._spi.write(msg)
        data = int.from_bytes(self._spi.read(2), 'big')
        self._cs.value(1)
        return data

    def readAngleRaw8B(self):
        msg = bytearray()
        msg.append(0x00)
        self._cs.value(0)
        self._spi.write(msg)
        data = int.from_bytes(self._spi.read(1), 'big')
        self._cs.value(1)
        return data

   

class MagAlpha:
    def __init__(self, spi_id, cs):
        self._spi = SPI_COM(spi_id=spi_id, cs=cs)

    def readAngle(self):
        raw_angle = self._spi.readAngleRaw16B()
        return (raw_angle * 360.0) / 65536.0

    @property
    def angle(self):
        return self.readAngle()
