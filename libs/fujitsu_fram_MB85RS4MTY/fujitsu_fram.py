import struct

from micropython import const
from machine import SPI, Pin

_MAX_SIZE_SPI = const(512 * 1024)

_SPI_MANF_ID = const(0x04)  # Read Manufacturer ID,
_SPI_PROD_ID = const(0xB42)  # Read Product ID
_SPI_OPCODE_RUID = const(0x4C)  # Read Unique ID

_SPI_OPCODE_WREN = const(0x06)  # Set write enable latch
_SPI_OPCODE_WRDI = const(0x04)  # Reset write enable latch
_SPI_OPCODE_RDSR = const(0x05)  # Read status register
_SPI_OPCODE_WRSR = const(0x01)  # Write status register

_SPI_OPCODE_WRITE = const(0x02)  # Write memory code
_SPI_OPCODE_READ = const(0x03)  # Read memory code
_SPI_OPCODE_FASTREAD = const(0x07)  # Fast read memory code

_SPI_OPCODE_DPD = const(0xBA)  # Deep Power Down Mode
_SPI_OPCODE_HIBERNATE = const(0xB9)  # Hibernate mode

_SPI_OPCODE_WRSN = const(0xC2)  # Write serial number
_SPI_OPCODE_RDSN = const(0xC3)  # Read serial number

_SPI_OPCODE_SSWR = const(0x42)  # Write special sector
_SPI_OPCODE_SSRD = const(0x4B)  # Read special sector
_SPI_OPCODE_FSSRD = const(0x49)
_SPI_OPCODE_RDID = const(0x9F)  # Read device ID


def float_to_bin(int_num):
    bits, = struct.unpack('!I', struct.pack('!f', int_num))
    return "{:032b}".format(bits)


def bin_to_float(binary_str):  # ieee-745 bits (max 32 bit)
    sign = int(binary_str[0])  # sign,     1 bit
    exp = int(binary_str[1:9], 2)  # exponent, 8 bits
    frac = int("1" + binary_str[9:], 2)  # fraction, len(N)-9 bits

    return (-1) ** sign * frac / (1 << (len(binary_str) - 9 - (exp - 127)))


class FRAM:
    def __init__(
            self,
            spi_bus,
            spi_cs,
            spi_sck,
            spi_mosi,
            spi_miso,
            write_protect: bool = False,
            wp_pin=None,
            wrap_around=True,
            baudrate: int = 4000000,
    ):
        self._spi = SPI(spi_bus, baudrate=baudrate, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
                        sck=Pin(spi_sck), mosi=Pin(spi_mosi), miso=Pin(spi_miso))

        self._wp = write_protect
        self._wraparound = wrap_around
        # MODES :
        # -> Initial - 0
        # -> Hibernate - 1
        # -> Deep Power Down - 2
        self._mode = 0

        self._cs_pin = Pin(spi_cs, Pin.OUT)

        if wp_pin:
            self._wp_pin = Pin(wp_pin, Pin.OUT)
        else:
            self._wp_pin = None

        self._max_size = _MAX_SIZE_SPI

        self._cs_pin.on()

        read_buffer = bytearray(4)
        self._cs_pin.off()
        self._spi.write(bytearray([_SPI_OPCODE_RDID]))
        self._spi.readinto(read_buffer)
        self._cs_pin.on()
        prod_id = (read_buffer[3] << 8) + (read_buffer[2])
        if (read_buffer[0] != _SPI_MANF_ID) and (prod_id != _SPI_PROD_ID):
            raise OSError("FRAM SPI device not found.")
        self._cs_pin.off()

    def _write(self, address: int, data: int, wraparound: bool = False, special: bool = 0, ) -> None:
        if (address + 1) > self._max_size:
            if wraparound:
                pass
            else:
                raise ValueError(
                    "Starting address + data length extends beyond"
                    " FRAM maximum address. Use 'wraparound=True' to"
                    " override this warning."
                )
        self._cs_pin.off()
        self._spi.write(bytearray([_SPI_OPCODE_WREN]))
        self._cs_pin.on()

        buffer = bytearray(4)
        if not special:
            buffer[0] = _SPI_OPCODE_WRITE
        else:
            buffer[0] = _SPI_OPCODE_SSWR
        buffer[1] = (address >> 16) & 0xFF
        buffer[2] = (address >> 8) & 0xFF
        buffer[3] = address & 0xFF
        self._cs_pin.off()
        self._spi.write(buffer)
        sent = bytearray([data])
        self._spi.write(sent)
        self._cs_pin.on()

        self._cs_pin.off()
        self._spi.write(bytearray([_SPI_OPCODE_WRDI]))
        self._cs_pin.on()

    def _read_address(self, address: int, read_buffer: bytearray, special: bool = 0) -> bytearray:
        write_buffer = bytearray(4)
        if not special:
            write_buffer[0] = _SPI_OPCODE_READ
        else:
            write_buffer[0] = _SPI_OPCODE_SSRD

        write_buffer[1] = (address >> 16) & 0xFF
        write_buffer[2] = (address >> 8) & 0xFF
        write_buffer[3] = address & 0xFF
        self._cs_pin.off()
        self._spi.write(write_buffer)
        self._spi.readinto(read_buffer)
        self._cs_pin.on()
        return read_buffer

    def wrsn(self, sn: bytearray):
        self._cs_pin.off()
        self._spi.write(bytearray([_SPI_OPCODE_WREN]))
        self._cs_pin.on()

        buffer = bytearray(9)
        buffer[0] = 0xC2
        buffer[1:9] = sn
        self._cs_pin.off()
        self._spi.write(buffer)
        self._cs_pin.on()

        self._cs_pin.off()
        self._spi.write(bytearray([_SPI_OPCODE_WRDI]))
        self._cs_pin.on()

    def rdsn(self):
        self._cs_pin.off()
        self._spi.write(bytearray([0xC3]))
        buffer = bytearray(8)
        self._spi.readinto(buffer)
        self._cs_pin.on()
        return int.from_bytes(buffer, "big")

    def read(self, address, special: bool = 0):
        if isinstance(address, int):
            if not 0 <= address < self._max_size:
                raise ValueError(
                    "Address '{0}' out of range. It must be 0 <= address < {1}.".format(
                        address, self._max_size
                    )
                )
            buffer = bytearray(1)
            return int.from_bytes(self._read_address(address, buffer, special), "little")
        raise ValueError("There is a problem in read")

    def write(self, address, value, special: bool = 0):
        if self.write_protected:
            raise RuntimeError("FRAM currently write protected.")

        if isinstance(address, int):
            if not isinstance(value, int):
                raise ValueError("Data stored in an address must be an integer 0-255")
            if not 0 <= address < self._max_size:
                raise ValueError(
                    "Address '{0}' out of range. It must be 0 <= address < {1}.".format(
                        address, self._max_size
                    )
                )
            self._write(address, value, self._wraparound, special)
            return

        raise ValueError("There is a problem in write")

    def hibernate_mode(self) -> bool:
        try:
            self._cs_pin.off()
            self._spi.write(bytearray([_SPI_OPCODE_HIBERNATE]))
            self._cs_pin.on()
            return True
        except Exception as e:
            print(e)
            return False

    def dpd_mode(self):
        try:
            self._cs_pin.off()
            self._spi.write(bytearray([_SPI_OPCODE_DPD]))
            self._cs_pin.on()
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def write_wraparound(self) -> bool:
        return self._wraparound

    @write_wraparound.setter
    def write_wraparound(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Write wraparound must be 'True' or 'False'.")
        self._wraparound = value

    @property
    def write_protected(self) -> bool:
        return self._wp if self._wp_pin is None else self._wp_pin.value

    @write_protected.setter
    def write_protected(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Write protected value must be 'True' or 'False'.")
        self._wp = value
        write_buffer = bytearray(2)
        write_buffer[0] = _SPI_OPCODE_WRSR
        if value:
            write_buffer[1] = 0x8C  # set WPEN, BP0, and BP1
        else:
            write_buffer[1] = 0x00  # clear WPEN, BP0, and BP1
        self._spi.write(write_buffer)
        if self._wp_pin is not None:
            self._wp_pin.value = value

    def write_int16(self, value: int, address: int, special: bool = 0):
        ba = int.to_bytes(value, 2, "big")
        self.write(address, ba[0], special)
        self.write(address + 1, ba[1], special)

    def write_int32(self, value: int, address: int, special: bool = 0):
        ba = int.to_bytes(value, 4, "big")
        self.write(address, ba[0], special)
        self.write(address + 1, ba[1], special)
        self.write(address + 2, ba[2], special)
        self.write(address + 3, ba[3], special)

    def read_int16(self, address: int, special: bool = 0):
        ba = bytearray(2)
        ba[0] = self.read(address, special)
        ba[1] = self.read(address + 1, special)
        value = int.from_bytes(ba, "big")
        return value

    def read_int32(self, address: int, special: bool = 0):
        ba = bytearray(4)
        ba[0] = self.read(address, special)
        ba[1] = self.read(address + 1, special)
        ba[2] = self.read(address + 2, special)
        ba[3] = self.read(address + 3, special)
        value = int.from_bytes(ba, "big")
        return value

    def write_float32(self, value: float, address: int, special: bool = 0):
        ieee754_str = float_to_bin(value)
        b1 = int(ieee754_str[:8], 2)
        b2 = int(ieee754_str[8:16], 2)
        b3 = int(ieee754_str[16:24], 2)
        b4 = int(ieee754_str[24:], 2)
        self.write(address, b1, special)
        self.write(address + 1, b2, special)
        self.write(address + 2, b3, special)
        self.write(address + 3, b4, special)

    def read_float32(self, address: int, special: bool = 0):
        ba = bytearray(4)
        ba[0] = self.read(address, special)
        ba[1] = self.read(address + 1, special)
        ba[2] = self.read(address + 2, special)
        ba[3] = self.read(address + 3, special)
        value = int.from_bytes(ba, "big")
        value = bin(value)[2:]
        value_length = len(value)
        if value_length < 32:
            temp = 32 - value_length
            return bin_to_float("0" * temp + value)
        else:
            return bin_to_float(value)

