import math
from machine import UART, Pin

_READ_COILS = 0x01
_READ_INPUT_STATUS = 0x02
_READ_HOLDING_REGISTERS = 0x03
_READ_INPUT_REGISTERS = 0x04

_WRITE_SINGLE_COIL = 0x05
_WRITE_SINGLE_REGISTER = 0x06
_WRITE_COILS = 0x15
_WRITE_REGISTERS = 0x10

BUFF_SIZE = 128

_ASCII_HEADER = ':'
_ASCII_FOOTER = '\r\n'

MODE_ASCII = 'ASCII'
MODE_RTU = 'RTU'

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


def calculateCRC(data):
    crc = 0xFFFF

    for c in data:
        crc = (crc >> 8) ^ CRC16table[(c ^ crc) & 0xFF]

    msb = (crc >> 8) & 0xFF
    lsb = crc & 0xFF
    return (lsb << 8) + msb


def calculateLRC(byte_data):
    total_dec = 0
    for b in byte_data:
        total_dec += b
    total_dec = -total_dec

    lrc = total_dec & 0xff
    return lrc


class Modbus:
    def __init__(self, uart_id, baudRate=9600, slaveID=0x01, tx=0, rx=1, parity=None, stop_bit=1, data_bits=8,
                 coils=None, input_status=None, holding_registers=None, input_registers=None, mode=MODE_RTU):
        self._slaveID = slaveID
        self._uart = UART(uart_id, baudRate, bits=data_bits, parity=parity, stop=stop_bit, tx=Pin(tx), rx=Pin(rx))
        self._mode = mode
        if coils:
            self.__coils = coils
        else:
            self.__coils = [0] * 50
        if holding_registers:
            self.__holding_registers = holding_registers
        else:
            self.__holding_registers = [0] * 50

        if input_registers:
            self.__input_registers = input_registers
        else:
            self.__input_registers = [0] * 50

        if input_status:
            self.__input_status = input_status
        else:
            self.__input_status = [0] * 50
        print("Slave device has been set you can use process(...) for communicating with mb master")
        print("Waiting for master device...")

    def listen(self):
        frame = self._uart.read(256)

        if frame is None:
            return

        if self._mode is MODE_ASCII:
            # Get the message as bytearray
            request_bytearray = bytearray()
            print(frame)
            for i in range(1, len(frame) - 2, 2):
                request_bytearray.append(int(frame[i:i + 2], 16))
            request_bytearray = list(request_bytearray)
        else:
            request_bytearray = list(frame)
        buffer_len = len(request_bytearray)
        sendArray = [0] * BUFF_SIZE
        # ------------------------------------------------------------- BUFFER LENGTH CHECK
        if buffer_len <= 6:
            print("BUFFER READ ERROR")
            return
        # ------------------------------------------------------------- SLAVE ID CHECK
        if request_bytearray[0] != self._slaveID:
            # command to another slave
            return
        if self._mode is MODE_ASCII:
            # ------------------------------------------------------------- LRC CHECK
            msg_lrc = request_bytearray[-1]
            if calculateLRC(request_bytearray[:-1]) != msg_lrc:
                print("LRC ERROR")
                return
        else:
            # ------------------------------------------------------------- CRC CHECK
            msg_crc = ((request_bytearray[buffer_len - 2] << 8) | request_bytearray[buffer_len - 1])
            if calculateCRC(request_bytearray[:buffer_len - 2]) != msg_crc:
                print("CRC ERROR")
                return
        # ------------------------------------------------------------- ADDRESS CHECK
        start_address = (request_bytearray[2] << 8) | request_bytearray[3]
        register_count = (request_bytearray[4] << 8) | request_bytearray[5]
        end_address = start_address + register_count
        if start_address > 256:
            return
        if end_address > 256:
            return
        function = request_bytearray[1]
        if (function == _READ_HOLDING_REGISTERS) or (function == _READ_INPUT_REGISTERS):
            no_of_bytes = register_count * 2
            responseFrameSize = 5 + no_of_bytes
            sendArray[0] = self._slaveID
            sendArray[1] = function
            sendArray[2] = no_of_bytes
            current_address = 3
            for index in range(start_address, end_address):
                temp = None
                if function == _READ_INPUT_REGISTERS:
                    temp = self.__input_registers[index]
                if function == _READ_HOLDING_REGISTERS:
                    temp = self.__holding_registers[index]
                sendArray[current_address] = temp >> 8
                current_address += 1
                sendArray[current_address] = temp & 0xFF
                current_address += 1
            if self._mode is MODE_ASCII:
                lrc8 = calculateLRC(sendArray[:current_address])
                sendArray[current_address] = lrc8
                current_address += 1
                ascii_text = ''.join(["{:02x}".format(a) for a in sendArray[:current_address]])
                ascii_full_text = _ASCII_HEADER + ascii_text + _ASCII_FOOTER
                self._uart.write(ascii_full_text.upper().encode())

            else:
                crc16 = calculateCRC(sendArray[:current_address])
                sendArray[responseFrameSize - 2] = crc16 >> 8
                sendArray[responseFrameSize - 1] = crc16 & 0xFF
                self._uart.write(bytearray(sendArray[:responseFrameSize]))
            return
        elif (function == _READ_COILS) or (function == _READ_INPUT_STATUS):
            no_of_bytes = math.ceil(register_count / 8)
            responseFrameSize = 5 + no_of_bytes
            sendArray[0] = self._slaveID
            sendArray[1] = function
            sendArray[2] = no_of_bytes
            address = 3
            byte_array = bytearray()
            decimals = [0] * 8
            for i in range(start_address, register_count, 8):
                if i + 8 < register_count:
                    if function == _READ_COILS:
                        decimals = [i for i in self.__coils[i:i + 8]][::-1]
                    if function == _READ_INPUT_STATUS:
                        decimals = [i for i in self.__input_status[i:i + 8]][::-1]
                elif i + 8 >= register_count:
                    if function == _READ_COILS:
                        decimals[8 - register_count:] = self.__coils[i:i + register_count % 8][::-1]
                    if function == _READ_INPUT_STATUS:
                        decimals[8 - register_count:] = self.__input_status[i:i + register_count % 8][::-1]

                bin_arr = ''
                for binary in decimals:
                    bin_arr = bin_arr + str(binary)
                #                 print(bin_arr)
                byte_array.append(int(bin_arr, 2))
            for byte in byte_array:
                sendArray[address] = byte
                address += 1

            if self._mode is MODE_ASCII:
                lrc8 = calculateLRC(sendArray[:address])
                sendArray[address] = lrc8
                address += 1
                ascii_text = ''.join(["{:02x}".format(a) for a in sendArray[:address]])
                ascii_full_text = _ASCII_HEADER + ascii_text + _ASCII_FOOTER
                self._uart.write(ascii_full_text.upper().encode())
            else:
                crc16 = calculateCRC(sendArray[:address])
                sendArray[responseFrameSize - 2] = crc16 >> 8
                sendArray[responseFrameSize - 1] = crc16 & 0xFF
                self._uart.write(bytearray(sendArray[:responseFrameSize]))
        elif function == _WRITE_SINGLE_REGISTER:
            self.__holding_registers[start_address] = register_count  # that register count is
            # actually the only registers itself

            if self._mode is MODE_ASCII:
                req_ba_len = len(request_bytearray)
                lrc8 = calculateLRC(request_bytearray[:-1])
                sendArray[:req_ba_len - 1] = request_bytearray[:-1]
                sendArray[req_ba_len] = lrc8
                ascii_text = ''.join(["{:02x}".format(a) for a in sendArray[:req_ba_len + 1]])
                ascii_full_text = _ASCII_HEADER + ascii_text + _ASCII_FOOTER
                self._uart.write(ascii_full_text.upper().encode())
            else:
                self._uart.write(bytearray(request_bytearray))

        elif function == _WRITE_SINGLE_COIL:
            if register_count == 0x00:
                self.__coils[start_address] = 0
            else:
                self.__coils[start_address] = 1
            if self._mode is MODE_ASCII:
                req_ba_len = len(request_bytearray)
                lrc8 = calculateLRC(request_bytearray[:-1])
                sendArray[:req_ba_len - 1] = request_bytearray[:-1]
                sendArray[req_ba_len] = lrc8
                ascii_text = ''.join(["{:02x}".format(a) for a in sendArray[:req_ba_len + 1]])
                ascii_full_text = _ASCII_HEADER + ascii_text + _ASCII_FOOTER
                self._uart.write(ascii_full_text.upper().encode())
            else:
                self._uart.write(bytearray(request_bytearray))

        elif function == _WRITE_REGISTERS:
            bytes_to_follow = request_bytearray[6]
            reg = 0
            for i in range(7, bytes_to_follow + 7, 2):
                self.__holding_registers[start_address + reg] = request_bytearray[i] << 8 | request_bytearray[i + 1]
                reg += 1
            sendArray[:6] = request_bytearray[:6]

            if self._mode is MODE_ASCII:
                lrc8 = calculateLRC(sendArray[:6])
                sendArray[6] = lrc8
                ascii_text = ''.join(["{:02x}".format(a) for a in sendArray[:7]])
                ascii_full_text = _ASCII_HEADER + ascii_text + _ASCII_FOOTER
                self._uart.write(ascii_full_text.upper().encode())
            else:
                crc16 = calculateCRC(sendArray[:6])
                sendArray[6] = crc16 >> 8
                sendArray[7] = crc16 & 0xFF
                self._uart.write(bytearray(sendArray[:8]))

        else:
            print("FUNCTION CODE ERROR")



