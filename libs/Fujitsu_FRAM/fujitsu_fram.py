from micropython import const
from machine import SPI, Pin
import utime

_MAX_SIZE_SPI = const(256*1024)

_SPI_MANF_ID = const(0x04)
_SPI_PROD_ID = const(0x302)

_SPI_OPCODE_WREN = const(0x06)  # Set write enable latch
_SPI_OPCODE_WRDI = const(0x04)  # Reset write enable latch
_SPI_OPCODE_RDSR = const(0x05)  # Read status register
_SPI_OPCODE_WRSR = const(0x01)  # Write status register
_SPI_OPCODE_READ = const(0x03)  # Read memory code
_SPI_OPCODE_WRITE = const(0x02)  # Write memory code
_SPI_OPCODE_RDID = const(0x9F)  # Read device ID

_SPI_OPCODE_SLEEP = const(0xB9)  # Sleep mode

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

    def _read_address(self, address: int, read_buffer: bytearray) -> bytearray:
        write_buffer = bytearray(4)
        write_buffer[0] = _SPI_OPCODE_READ
        if self._max_size > 0xFFFF:
            write_buffer[1] = (address >> 16) & 0xFF
            write_buffer[2] = (address >> 8) & 0xFF
            write_buffer[3] = address & 0xFF
        else:
            write_buffer[1] = (address >> 8) & 0xFF
            write_buffer[2] = address & 0xFF
        self._cs_pin.off()
        self._spi.write(write_buffer)
        self._spi.readinto(read_buffer)
        self._cs_pin.on()
        return read_buffer

    def _write(self, start_address: int, data, wraparound: bool = False,
               ) -> None:
        buffer = bytearray(4)
        if not isinstance(data, int):
            data_length = len(data)
        else:
            data_length = 1
            data = [data]
        if (start_address + data_length) > self._max_size:
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
        buffer[0] = _SPI_OPCODE_WRITE
        if self._max_size > 0xFFFF:
            buffer[1] = (start_address >> 16) & 0xFF
            buffer[2] = (start_address >> 8) & 0xFF
            buffer[3] = start_address & 0xFF
        else:
            buffer[1] = (start_address >> 8) & 0xFF
            buffer[2] = start_address & 0xFF
        self._cs_pin.off()
        self._spi.write(buffer)
        for i in range(0, data_length):
            self._cs_pin.off()
            self._spi.write(bytearray([data[i]]))
            self._cs_pin.on()
        self._spi.write(bytearray([_SPI_OPCODE_WRDI]))
        self._cs_pin.on()

    def sleep(self) -> bool:
        try:
            self._cs_pin.off()
            self._spi.write(bytearray([_SPI_OPCODE_SLEEP]))
            self._cs_pin.on()
            return True
        except Exception as e:
            print(e)
            return False
        

    def wake_up(self):
        self._cs_pin.off()
        utime.sleep_ms(400)
        self._cs_pin.on()

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

    def __len__(self) -> int:
        return self._max_size

    def __getitem__(self, address) -> bytearray:
        if isinstance(address, int):
            if not 0 <= address < self._max_size:
                raise ValueError(
                    "Address '{0}' out of range. It must be 0 <= address < {1}.".format(
                        address, self._max_size
                    )
                )
            buffer = bytearray(1)
            read_buffer = self._read_address(address, buffer)
        elif isinstance(address, slice):
            if address.step is not None:
                raise ValueError("Slice stepping is not currently available.")

            regs = list(
                range(
                    address.start if address.start is not None else 0,
                    address.stop if address.stop is not None else self._max_size,
                )
            )
            if regs[0] < 0 or (regs[0] + len(regs)) > self._max_size:
                raise ValueError(
                    "Address slice out of range. It must be 0 <= [starting address"
                    ":stopping address] < {0}.".format(self._max_size)
                )

            buffer = bytearray(len(regs))
            read_buffer = self._read_address(regs[0], buffer)
        else:
            return bytearray([0x00])
        return int(read_buffer[0])

    def __setitem__(self, address, value):
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

            self._write(address, value, self._wraparound)

        elif isinstance(address, slice):
            if not isinstance(value, (bytes, bytearray, list, tuple)):
                raise ValueError(
                    "Data must be bytes, bytearray, list, "
                    "or tuple for multiple addresses"
                )
            if (address.start is None) or (address.stop is None):
                raise ValueError("Boundless slices are not supported")
            if (address.step is not None) and (address.step != 1):
                raise ValueError("Slice stepping is not currently available.")
            if (address.start < 0) or (address.stop > self._max_size):
                raise ValueError(
                    "Slice '{0}:{1}' out of range. All addresses must be 0 <= address < {2}.".format(
                        # pylint: disable=line-too-long
                        address.start, address.stop, self._max_size
                    )
                )
            if len(value) < (len(range(address.start, address.stop))):
                raise ValueError(
                    "Cannot set values with a list smaller than the number of indexes"
                )

            self._write(address.start, value, self._wraparound)

