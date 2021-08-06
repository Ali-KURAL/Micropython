import modbus
import time


modbus_obj = modbus.Modbus(0,9600,0x01,10,16,17)

register_quantity=10
signed=True

registers = [1]*10
while True:    
    modbus_obj.process(registers)
    registers[1] += 1
    time.sleep(0.5)