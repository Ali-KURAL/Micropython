'''
master_main.py - An example MicroPython project, using the micropython-modbus 
library. 

This example code is dedicated to the public domain. To the extent possible 
under law, Extel Technologies has waived all copyright and related or 
neighboring rights to "master_main.py". This work is published from: Australia. 

https://creativecommons.org/publicdomain/zero/1.0/
'''

import logging
import machine
import struct
import time
import modbus
import modbus.defines as cst
from modbus import modbus_rtu


LOGGER = logging.getLogger("main")
LOGGER.setLevel(logging.DEBUG)





LOGGER.info("Opening UART0")
uart = machine.UART(0, 9600, bits=8, parity=None, stop=1, timeout=1000, timeout_char=50)

master = modbus_rtu.RtuMaster(uart)


LOGGER.info("Reading from register 0x00")
# 'execute' returns a pair of 16-bit words
f_word_pair = master.execute(0x01, cst.WRITE_SINGLE_REGISTER, 0x00, output_value = 10)
print(f_word_pair)
# Re-pack the pair of words into a single byte, then un-pack into a float
volts = struct.unpack('<f', struct.pack('<h', int(f_word_pair[1])) + struct.pack('<h', int(f_word_pair[0])))[0]

LOGGER.info("Reading from register 0x06")
# 'execute' returns a pair of 16-bit words
f_word_pair = master.execute(0x01, cst.READ_HOLDING_REGISTERS, 0x00, 2)
print(f_word_pair)
# Re-pack the pair of words into a single byte, then un-pack into a float
amps = struct.unpack('<f', struct.pack('<h', int(f_word_pair[1])) + struct.pack('<h', int(f_word_pair[0])))[0]

print("DONE")




while True:
    f_word_pair = master.execute(0x01, cst.READ_HOLDING_REGISTERS, 0x06, 1)
    print(f_word_pair)
    time.sleep(1)
    
