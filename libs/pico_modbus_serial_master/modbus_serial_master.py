import math
import struct
import time
from machine import UART, Pin

_ASCII_HEADER = ':'
_ASCII_FOOTER = '\r\n'

MODE_ASCII = 'ASCII'
MODE_RTU = 'RTU'


def floatToBinary32(value):
    bits, = struct.unpack('!I', struct.pack('!f', value))
    return "{:032b}".format(bits)


def floatToBinary64(value):
    packed = struct.pack('!d', value)
    bits, = struct.unpack('!Q', packed)
    return "{:064b}".format(bits)


def calculate_lrc(data):
    total_dec = 0
    for i in range(0, len(data), 2):
        total_dec += 16 * int(data[i], 16) + int(data[i + 1], 16)
    total_dec = -total_dec

    lrc = int(hex(total_dec), 16) & 0xff
    return lrc


def calculateCRC(data):
    CRC16table = (
        0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
        0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
        0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
        0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
        0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
        0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
        0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
        0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
        0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
        0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
        0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
        0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
        0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
        0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
        0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
        0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
        0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
        0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
        0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
        0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
        0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
        0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
        0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
        0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
        0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
        0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
        0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
        0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
        0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
        0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
        0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
        0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
    )
    crc = 0xFFFF

    for c in data:
        crc = (crc >> 8) ^ CRC16table[(c ^ crc) & 0xFF]

    msb = (crc >> 8) & 0xFF
    lsb = crc & 0xFF
    return (lsb << 8) + msb


def sendCommand(slave, func_code, starting_address, total_size, registers=None, read=True, waitForResponse=0.1,
                mode=MODE_RTU):
    if registers is None:
        registers = []
    msg_bytearray = bytearray()
    msg_bytearray.append(slave.getSlaveID())
    if (func_code is 16) and (registers is not None):
        msg_bytearray.append(func_code)
        msg_bytearray.append(starting_address >> 8)
        msg_bytearray.append(starting_address & 0xFF)
        msg_bytearray.append(total_size >> 8)
        msg_bytearray.append(total_size & 0xFF)
        msg_bytearray.append(total_size * 2)
        for reg in registers:
            msg_bytearray.append(reg >> 8)
            msg_bytearray.append(reg & 0xFF)
    else:
        msg_bytearray.append(func_code)
        msg_bytearray.append(starting_address >> 8)
        msg_bytearray.append(starting_address & 0xFF)
        msg_bytearray.append(total_size >> 8)
        msg_bytearray.append(total_size & 0xFF)

    if mode is MODE_ASCII:
        ascii_bytearray = ''.join(["{:02x}".format(a) for a in msg_bytearray])
        lrc = calculate_lrc(ascii_bytearray)
        lrc = hex(lrc).replace("0x", "")
        ascii_bytearray = _ASCII_HEADER + ascii_bytearray + lrc + _ASCII_FOOTER
        slave.uart.write(ascii_bytearray.upper())
    else:
        crc = calculateCRC(msg_bytearray)
        msg_bytearray.append(crc >> 8)
        msg_bytearray.append(crc & 0xFF)
        slave.uart.write(msg_bytearray)

    if read is True:
        time.sleep(waitForResponse)
        bytes_in_order = slave.uart.any()
        return slave.uart.read(bytes_in_order)
    # print(msg_bytearray)
    return True


class Slave:
    def __init__(self, port, uart_tx, uart_rx, slaveID=1, baudrate=9600, parity=None, bits=8, stop=1, mode=MODE_RTU):
        self._slaveID = slaveID
        self._port = port
        self._mode = mode
        self._uart = UART(port, baudrate,
                          tx=Pin(uart_tx),
                          rx=Pin(uart_rx),
                          bits=bits,
                          parity=parity,
                          stop=stop)

    def getSlaveID(self):
        return self._slaveID

    def getPort(self):
        return self._port

    def flush(self):
        flushed = self._uart.any()
        self._uart.read(flushed)

    @property
    def mode(self):
        return self._mode

    @property
    def uart(self):
        return self._uart


class Master:
    def __init__(self):
        self._slaves = dict()
        self._log = ""
        self._log_count = 0

    def _printToLog(self, string):
        self._log_count += 1
        self._log += str(self._log_count) + string + "\n"

    def printLog(self):
        print(self._log)

    def addSlave(self, slave):
        if slave.getSlaveID() not in self._slaves.keys():
            self._printToLog("Slave " + str(slave.getSlaveID) + " added to slaves dictionary." + str(slave.getPort()))
            self._slaves[slave.getSlaveID()] = slave
        else:
            self._printToLog("Slave " + slave.getSlaveID + "already in dictionary")

    # FC01
    def readCoils(self, slaveID, starting_address, total_size):
        slave = self._slaves[slaveID]
        slave.flush()
        sendCommand(slave, 1, starting_address, total_size, read=False)
        no_of_bytes = math.ceil(total_size / 8)
        responseFrameSize = 5 + no_of_bytes
        resp_coil_array = []
        resp_bytearray = slave.uart.read(responseFrameSize)
        slave.uart.flush()
        space_holder = no_of_bytes * 8 - total_size

        def get_bin(x, n):
            return format(x, 'b').zfill(n)

        for i in range(3, responseFrameSize - 2):
            coils = get_bin(resp_bytearray[i], 8)
            for j in range(8):
                if i == responseFrameSize - 3:
                    resp_coil_array.append(coils[j + space_holder])
                    if (j + space_holder + 1) is len(coils):
                        continue
                else:
                    resp_coil_array.append(coils[j])

        return resp_coil_array

    # FC02
    def readInputStatus(self, slaveID, starting_address, total_size):
        return self.readCoils(slaveID, starting_address, total_size)

    # FC03
    def readHoldingRegisters(self, slaveID, starting_address, total_size):
        slave = self._slaves[slaveID]
        slave.flush()
        sendCommand(slave, 3, starting_address, total_size, read=False, mode=slave.mode)
        resp_reg_array = ["ERROR"]
        if slave.mode is MODE_ASCII:
            no_of_bytes = total_size * 2
            responseFrameSize = (no_of_bytes + 5) * 2
            time.sleep(0.1)
            resp_bytearray = slave.uart.read(responseFrameSize)
            if resp_bytearray is None:
                raise Exception("Check the connection of RS485")
            resp_bytearray = str(resp_bytearray)[3:]
            no_of_bytes = int(resp_bytearray[4:6], 16)
            resp_reg_array = []
            register_string = resp_bytearray[6:6 + no_of_bytes * 2]
            reg_index = 0
            for i in range(0, no_of_bytes * 2, 4):
                resp_reg_array.append(int(register_string[i:i + 4], 16))
                reg_index += 1
            lrc = calculate_lrc(resp_bytearray[:-5])
            if lrc is not int(resp_bytearray[-5:-3], 16):
                raise ValueError("LRC ERROR")

        if slave.mode is MODE_RTU:
            no_of_bytes = total_size * 2
            responseFrameSize = no_of_bytes + 5
            time.sleep(0.1)
            resp_bytearray = slave.uart.read(responseFrameSize)
            if resp_bytearray is None:
                raise Exception("Check the connection of RS485")
            resp_reg_array = []
            for i in range(3, responseFrameSize - 2, 2):
                resp_reg_array.append((resp_bytearray[i] << 8) | resp_bytearray[i + 1])

            crc = calculateCRC(resp_bytearray[:responseFrameSize - 2])
            if crc is not ((resp_bytearray[responseFrameSize - 2] << 8) | resp_bytearray[responseFrameSize - 1]):
                ValueError("CRC ERROR")
        return resp_reg_array

    # FC04
    def readInputRegisters(self, slaveID, starting_address, total_size):
        slave = self._slaves[slaveID]
        slave.flush()
        return self.readHoldingRegisters(slave, starting_address, total_size)

    # FC05
    def forceSingleCoil(self, slaveID, address, value):
        try:
            slave: Slave = self._slaves[slaveID]
            response = sendCommand(slave, 5, address, value, mode=slave.mode)
            if len(response) > 0:
                slave.flush()
                return True
        except Exception as e:
            print(e)
            return False

    # FC06
    def writeSingleRegister(self, slaveID, address, value):
        try:
            slave: Slave = self._slaves[slaveID]
            response = sendCommand(slave, 6, address, value, mode=slave.mode)
            if len(response) > 0:
                slave.flush()
                return True

        except Exception as e:
            print(e)
            return False

    # FC16
    def writeMultipleRegisters(self, slaveID, address, values):
        try:
            slave = self._slaves[slaveID]
            response = sendCommand(slave, 16, address, len(values), registers=values, mode=slave.mode)
            if len(response) > 0:
                slave.flush()
                return True
            return False

        except Exception as e:
            print(e)
            return False

    def writeInteger(self, address, value, slaveID=1):
        try:
            self.writeSingleRegister(slaveID, address, value)
        except Exception as e:
            return e
        else:
            return True

    def writeLong(self, address, value, slaveID=1):
        try:
            self.writeSingleRegister(slaveID, address, value >> 16)
            self.writeSingleRegister(slaveID, address + 1, value & 0xFFFF)
        except Exception as e:
            return e
        else:
            return True

    def readLong(self, address, slaveID=1):
        long_integers = self.readHoldingRegisters(slaveID, address, 2)
        return (long_integers[0] << 16) | (long_integers[1] & 0xFFFF)

    def writeFloat(self, address, new_value, slaveID=1):
        ieee754_str: str = floatToBinary32(new_value)
        i1 = int(ieee754_str[:16], 2)
        i2 = int(ieee754_str[16:], 2)
        # print(b1, b2)
        # print(ieee754_str)
        return self.writeMultipleRegisters(slaveID, address, [i1, i2])

    def readFloat(self, address, slaveID=1):
        float_integers = self.readHoldingRegisters(slaveID, address, 2)
        float_bytes = bytearray([float_integers[0] >> 8, float_integers[0] & 0xFF,
                                 float_integers[1] >> 8, float_integers[1] & 0xFF])
        return struct.unpack(">f", float_bytes)[0]

    def writeDouble(self, address, new_value, slaveID=1):
        ieee754_str: str = floatToBinary64(new_value)
        i1 = int(ieee754_str[:16], 2)
        i2 = int(ieee754_str[16:32], 2)
        i3 = int(ieee754_str[32:48], 2)
        i4 = int(ieee754_str[48:], 2)
        # print(b1, b2)
        # print(ieee754_str)
        return self.writeMultipleRegisters(slaveID, address, [i1, i2, i3, i4])

    def readDouble(self, address, slaveID=1):
        float_integers = self.readHoldingRegisters(slaveID, address, 4)
        float_bytes = bytearray(
            [float_integers[0] >> 8, float_integers[0] & 0xFF, float_integers[1] >> 8, float_integers[1] & 0xFF,
             float_integers[2] >> 8, float_integers[2] & 0xFF, float_integers[3] >> 8, float_integers[3] & 0xFF])
        return struct.unpack(">d", float_bytes)[0]
