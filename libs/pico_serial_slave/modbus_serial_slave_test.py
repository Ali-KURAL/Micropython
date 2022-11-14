
import time
from modbus_serial_slave import Modbus

holding_registers = [0] * 10
mb_obj = Modbus(0,holding_registers = holding_registers)


while True:
    mb_obj.listen()
    time.sleep(0.5)